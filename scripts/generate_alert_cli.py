#!/usr/bin/env python3
"""
Генерирует команды для создания notification channels и alert'ов в Yandex Monitoring.
"""

from __future__ import annotations

import argparse
from typing import Dict

import yaml


def _parse_var(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("--var должен быть в формате KEY=VALUE")
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError("Имя переменной в --var не может быть пустым")
    return key, value.strip()


def _apply_vars(text: str, replacements: Dict[str, str]) -> str:
    result = text
    for key, value in replacements.items():
        result = result.replace(f"<{key}>", value)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Monitoring alert commands")
    parser.add_argument("--spec", default="monitoring_alerts.yaml", help="YAML spec file")
    parser.add_argument(
        "--channels-only",
        action="store_true",
        help="Генерировать только команды создания notification channels",
    )
    parser.add_argument(
        "--alerts-only",
        action="store_true",
        help="Генерировать только команды alert'ов",
    )
    parser.add_argument(
        "--var",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Заменить плейсхолдер <KEY> на VALUE в выводе",
    )
    args = parser.parse_args()

    if args.channels_only and args.alerts_only:
        parser.error("Нельзя одновременно указывать --channels-only и --alerts-only")

    replacements: Dict[str, str] = {}
    for raw in args.var:
        key, value = _parse_var(raw)
        replacements[key] = value

    with open(args.spec, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f) or {}

    include_channels = not args.alerts_only
    include_alerts = not args.channels_only

    if include_channels:
        for channel in spec.get("notification_channels", []):
            if channel.get("type") == "email":
                command = (
                    "yc monitoring notification-channel create email "
                    f"--name {channel['name']} --email {channel['email']}"
                )
                print(_apply_vars(command, replacements))

    if include_alerts:
        for alert in spec.get("alerts", []):
            base = (
                "yc monitoring alert create "
                f"--name {alert['name']} "
                f"--metric {alert['metric']} "
                f"--comparison {alert.get('comparison', 'GT')} "
                f"--threshold {alert.get('threshold', 0)} "
                f"--aggregation {alert.get('aggregation', 'mean')} "
                f"--period \"{alert.get('period', '5m')}\" "
                f"--notification-channel-id {alert['channel_id']} "
            )
            labels = " ".join(
                f"--labels {key}={value}" for key, value in alert.get("labels", {}).items()
            )
            print(_apply_vars(base + labels, replacements))


if __name__ == "__main__":
    main()
