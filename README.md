# VSM Restaurant

# Cheatsheet
## Alembic
### Генерация новых миграций
alembic revision --autogenerate -m "Add demo model"

Hint: Не забудьте добавить импорт новых моделей в vsm_restaurant/db/__init__.py

Пример запуска:
```
(.venv) ➜  vsm-restaurant git:(main) ✗ alembic revision --autogenerate -m "Add demo model"
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'demo'
INFO  [alembic.autogenerate.compare] Detected added index 'demo_timestamp_idx' on '('timestamp',)'
  Generating /Users/wutiarn/PycharmProjects/miit/vsm-restaurant/alembic/versions/61d371fd62af_add_demo_model.py ...  done
```
```
(.venv) ➜  vsm-restaurant git:(main) ✗ alembic revision --autogenerate -m "Add json data to demo"
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.ddl.postgresql] Detected sequence named 'demo_id_seq' as owned by integer column 'demo(id)', assuming SERIAL and omitting
INFO  [alembic.autogenerate.compare] Detected added column 'demo.json_data'
  Generating /Users/wutiarn/PycharmProjects/miit/vsm-restaurant/alembic/versions/5ad79c711b2f_add_json_data_to_demo.py ...  done
  ```
