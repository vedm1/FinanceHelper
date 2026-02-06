.PHONY: env-pull env-push api frontend

env-pull:
	@./.env-scripts/bw-pull.sh

env-push:
	@./.env-scripts/bw-push.sh

api:
	uvicorn backend.api:app --reload --port 8000

frontend:
	cd frontend && npm run dev