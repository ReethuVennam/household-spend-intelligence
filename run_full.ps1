$ErrorActionPreference = "Stop"
python -m src.cli all --scale full --seed 20261022 --out dataset --formats csv,json,sql
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m src.cli reproduce --scale full --seed 20261022 --formats csv --out dataset
exit $LASTEXITCODE
