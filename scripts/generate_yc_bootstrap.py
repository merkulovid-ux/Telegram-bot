#!/usr/bin/env python3
"""Генератор команд для первичной настройки YC инфраструктуры."""

from __future__ import annotations

import argparse
from textwrap import dedent


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder-id", default="<folder-id>")
    parser.add_argument("--registry-id", default="<registry-id>")
    parser.add_argument("--container-id", default="<container-id>")
    parser.add_argument("--secret-id", default="<lockbox-secret-id>")
    parser.add_argument("--runtime-sa", default="telegram-runtime")
    parser.add_argument("--deploy-sa", default="telegram-deploy")
    parser.add_argument("--build-sa", default="telegram-build")
    parser.add_argument("--image-tag", default="$BUILD_ID")
    return parser.parse_args()


def print_section(title: str, body: str) -> None:
    line = "=" * len(title)
    print(f"\n{title}\n{line}\n{body.strip()}\n")


def main() -> None:
    args = build_args()
    folder = args.folder_id
    runtime = args.runtime_sa
    deploy = args.deploy_sa
    build = args.build_sa
    registry = args.registry_id
    secret = args.secret_id
    tag = args.image_tag

    print_section(
        "Service Accounts",
        dedent(
            f"""
            yc iam service-account create --name {runtime}
            yc iam service-account create --name {deploy}
            yc iam service-account create --name {build}

            # после создания подставьте ID сервисных аккаунтов вместо <*_sa_id>
            yc resource-manager folder add-access-binding --id {folder} \
              --role serverless.containers.admin --subject serviceAccount:<runtime_sa_id>
            yc resource-manager folder add-access-binding --id {folder} \
              --role lockbox.payloadViewer --subject serviceAccount:<runtime_sa_id>
            yc resource-manager folder add-access-binding --id {folder} \
              --role deploy.editor --subject serviceAccount:<deploy_sa_id>
            yc resource-manager folder add-access-binding --id {folder} \
              --role container-registry.pusher --subject serviceAccount:<deploy_sa_id>
            yc resource-manager folder add-access-binding --id {folder} \
              --role cloud-build.builder --subject serviceAccount:<build_sa_id>
            yc resource-manager folder add-access-binding --id {folder} \
              --role devtools.repo-reader --subject serviceAccount:<build_sa_id>
            """
        ),
    )

    print_section(
        "Lockbox",
        dedent(
            f"""
            python export_lockbox_payload.py --env .env --env .env.prod --output secrets.json
            yc lockbox secret create --name telegram-ai-bot --payload-file secrets.json
            yc lockbox secret add-version --id {secret} --payload-file secrets.json
            """
        ),
    )

    print_section(
        "Container Registry & Docker",
        dedent(
            f"""
            yc container registry create --name telegram-ai-registry
            docker build -t cr.yandex/{registry}/telegram-ai-bot:{tag} .
            docker push cr.yandex/{registry}/telegram-ai-bot:{tag}
            """
        ),
    )

    print_section(
        "Cloud Deploy",
        dedent(
            f"""
            yc deploy release run \
              --spec deploy-spec.yaml \
              --service-account-id <deploy_sa_id> \
              --labels build_id={tag}

            # либо напрямую
            yc serverless container revision deploy \
              --container-id {args.container_id} \
              --image cr.yandex/{registry}/telegram-ai-bot:{tag} \
              --service-account-id <runtime_sa_id> \
              --secrets TELEGRAM_BOT_TOKEN={secret}:TELEGRAM_BOT_TOKEN
            """
        ),
    )

    print_section(
        "Monitoring",
        dedent(
            """
            python scripts/generate_alert_cli.py --spec monitoring_alerts.yaml \
              --var channel-id=<channel-id> \
              --var container-id=<container-id> \
              --var kb-diag-job-id=<job-id>
            """
        ),
    )


if __name__ == "__main__":
    main()
