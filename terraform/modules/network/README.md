# Network Module (Cloud.ru)

Создаёт базовую сетевую инфраструктуру в Cloud.ru:

- VPC (`sbercloud_vpc_v1`) с заданным CIDR.
- Один или несколько сабнетов (`sbercloud_vpc_subnet_v1`) для разных AZ.
- Security Group + ingress/egress правила для приложений Telegram AI Bot.

## Входные переменные

| Переменная | Тип | Описание |
| --- | --- | --- |
| `vpc_name` | string | Имя VPC. |
| `vpc_cidr` | string | CIDR блока (например, `10.20.0.0/16`). |
| `subnets` | list(object) | Список подсетей (name, cidr, gateway_ip, availability_zone). |
| `security_group_name` | string | Имя security group (по умолчанию `telegram-ai-bot-sg`). |
| `security_group_description` | string | Описание SG. |
| `security_group_rules` | list(object) | Пользовательские ingress правила (по умолчанию HTTP/HTTPS из любого источника). |

## Выходы

| Output | Описание |
| --- | --- |
| `vpc_id` | ID созданного VPC. |
| `subnet_ids` | Map `имя -> ID` всех подсетей. |
| `security_group_id` | ID security group по умолчанию. |

## Использование

```hcl
module "network" {
  source = "./modules/network"

  vpc_name = "telegram-ai-bot"
  vpc_cidr = "10.20.0.0/16"
  subnets = [
    {
      name              = "app-a"
      cidr              = "10.20.1.0/24"
      gateway_ip        = "10.20.1.1"
      availability_zone = "ru-moscow-1a"
    }
  ]
}
```

Модуль будет расширяться по мере уточнения требований (например, добавление приватных/публичных подсетей, NAT, дополнительных правил SG). Все изменения согласовываем через задачи BL-15/BL-18.

