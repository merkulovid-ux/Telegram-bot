# Чеклист миграции на Cloud.ru

## Подготовка (Pre-migration)

### 1. IAM & Service Accounts ✅
- [x] Создать сервисный аккаунт `Secret_Management-sa`
- [x] Получить Service Account ID: `52b69061-6b4e-4ca9-9446-0d619feb3d31`
- [x] Сгенерировать access_key/secret_key для OBS
- [x] Настроить IAM роли с минимальными правами

### 2. Terraform Setup ✅
- [x] Установить Terraform >= 1.5.0
- [x] Настроить SberCloud provider
- [x] Создать OBS бакет для state
- [x] Настроить backend configuration
- [x] Загрузить credentials в GitHub Secrets

### 3. Network Infrastructure 🔄
- [x] Создать VPC (terraform/modules/network)
- [ ] Настроить подсети (public/private)
- [ ] Создать Security Groups
- [ ] Проверить connectivity

## Фаза 1: Infrastructure as Code

### 4. Managed PostgreSQL 🔄
- [x] Изучить API и Terraform ресурсы
- [ ] Создать модуль managed_pg
- [ ] Настроить pgvector extension
- [ ] Создать пользователей и базу данных
- [ ] Протестировать подключение

### 5. Object Storage (OBS) 🔄
- [x] Создать бакет для Terraform state ✅
- [x] Настроить bucket policy ✅
- [ ] Создать бакет для данных приложения
- [ ] Настроить lifecycle policies
- [ ] Протестировать upload/download

### 6. Vault (Secrets Management) ⏳
- [ ] Изучить Vault API
- [ ] Создать секреты для БД
- [ ] Настроить доступ для приложений
- [ ] Интегрировать с Terraform

## Фаза 2: Application Migration

### 7. Container Apps ⏳
- [ ] Изучить API и Terraform ресурсы
- [ ] Создать environment
- [ ] Настроить scaling rules
- [ ] Интегрировать с Artifact Registry

### 8. CI/CD Pipeline ⏳
- [ ] Настроить GitHub Actions
- [ ] Интегрировать с Container Apps
- [ ] Настроить automated deployment
- [ ] Добавить security scanning

### 9. Application Code Changes ⏳
- [ ] Обновить конфигурацию для Cloud.ru endpoints
- [ ] Заменить Yandex SDK на GigaChat
- [ ] Интегрировать Vault для секретов
- [ ] Обновить database connections

## Фаза 3: Data Migration

### 10. Database Migration ⏳
- [ ] Создать дамп текущей БД
- [ ] Загрузить в OBS
- [ ] Восстановить в Cloud.ru PostgreSQL
- [ ] Протестировать data integrity

### 11. File Storage Migration ⏳
- [ ] Перенести PDF документы в OBS
- [ ] Обновить пути в приложении
- [ ] Протестировать RAG functionality

## Фаза 4: Testing & Validation

### 12. Integration Testing ⏳
- [ ] Настроить тестовую среду
- [ ] Протестировать все endpoints
- [ ] Проверить performance
- [ ] Validate security

### 13. Monitoring & Alerting ⏳
- [ ] Настроить Cloud.ru Monitoring
- [ ] Создать алерты
- [ ] Интегрировать логирование
- [ ] Настроить dashboards

## Фаза 5: Production Deployment

### 14. Staging Environment ⏳
- [ ] Развернуть staging
- [ ] Провести end-to-end testing
- [ ] Получить feedback от команды

### 15. Production Cutover ⏳
- [ ] Финализировать production environment
- [ ] Выполнить data migration
- [ ] Переключить traffic
- [ ] Monitor post-migration

### 16. Post-Migration Activities ⏳
- [ ] Удалить старые ресурсы
- [ ] Обновить документацию
- [ ] Провести retrospective
- [ ] Оптимизировать costs

## Risk Mitigation

### Critical Risks
- **Data Loss**: Регулярные бэкапы, тестирование восстановления
- **Downtime**: Blue-green deployment, gradual rollout
- **API Changes**: Version pinning, compatibility testing
- **Cost Overrun**: Budget alerts, resource monitoring

### Dependencies
- Service Account ID: ✅ Получен
- Access Keys: ✅ Сгенерированы
- OBS Bucket: ✅ Создан
- Terraform Backend: 🔄 Настраивается

## Success Criteria

- [ ] Infrastructure deployed via Terraform
- [ ] Application running in Container Apps
- [ ] Database migrated successfully
- [ ] All tests passing
- [ ] Performance >= current levels
- [ ] Security policies enforced
- [ ] Monitoring and alerting configured
- [ ] Team trained on new platform

## Timeline (Estimated)

- **Phase 1**: 1-2 недели (Infrastructure)
- **Phase 2**: 1 неделя (Application)
- **Phase 3**: 3-5 дней (Data Migration)
- **Phase 4**: 1 неделя (Testing)
- **Phase 5**: 1 день (Cutover)

## Resources Required

### Team
- DevOps Engineer (2-3 человека)
- Backend Developer (1-2 человека)
- QA Engineer (1 человек)

### Cloud.ru Services
- Service Account с admin правами
- Budget approval для ресурсов
- Support access для troubleshooting

### Tools
- Terraform >= 1.5.0
- Docker for containerization
- GitHub Actions for CI/CD
- Monitoring tools

## Emergency Rollback Plan

1. **Immediate rollback**: Switch back to Yandex Cloud
2. **Gradual rollback**: Keep both environments running
3. **Data recovery**: Use backups for restore
4. **Communication**: Notify users about issues

## Next Steps

1. **Immediate**: Завершить настройку Terraform backend
2. **Short-term**: Создать VPC и PostgreSQL через Terraform
3. **Medium-term**: Мигрировать application code
4. **Long-term**: Полная production migration

---

*Этот чеклист будет обновляться по мере прогресса миграции и получения новой информации из документации Cloud.ru.*


