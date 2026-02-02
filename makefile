.PHONY: env-pull env-push

env-pull:
	@./.env-scripts/bw-pull.sh

env-push:
	@./.env-scripts/bw-push.sh