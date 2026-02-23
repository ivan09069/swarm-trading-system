# Security Policy

## Reporting a Vulnerability

Please do **not** open a public issue for security vulnerabilities.  
Email the maintainer directly or use GitHub's private vulnerability reporting feature.

## Hardcoded-Secret Remediation

This repository previously contained plaintext private keys and seed phrases in the
working tree. Those secrets have been removed from the code in this PR.

### Steps taken in this PR
1. All private keys, seed phrases, and addresses are now loaded at runtime from:
   - A gitignored JSON file (e.g. `wallets.json`, `seeds.json`, `targets.json`, `addresses.json`)
   - Or an environment variable (`CONTROLLED_WALLETS_JSON`, `KEYMATCHER_SEEDS_JSON`, etc.)
   - Or indexed `WALLET_{i}_*` / `SEED_{i}_*` environment variables
2. No secret values are printed to stdout or logs.
3. `.gitignore` has been hardened to prevent committing secret files.
4. Example files (`*.example.json`) with placeholder values are provided.

### Git history purge (to be done by repo owner after merge)

Even after merging this PR the secrets remain in git history. To fully purge them:

```bash
# 1. Install BFG Repo Cleaner (https://rtyley.github.io/bfg-repo-cleaner/)
#    Download bfg.jar from the releases page.

# 2. Create a file listing the literal secrets to remove, one per line:
#    secrets.txt

# 3. Clone a fresh mirror of the repo
git clone --mirror https://github.com/YOUR_ORG/YOUR_REPO.git

# 4. Run BFG
java -jar bfg.jar --replace-text secrets.txt swarm-trading-system.git

# 5. Clean and force-push
cd swarm-trading-system.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force

# 6. All collaborators must re-clone after the force-push.
```

> **Important:** After force-pushing, any forks or local clones will still have
> the old history. Treat all previously committed keys as **compromised** and
> rotate/revoke them immediately.

## Secret Management Best Practices

- Store secrets in a password manager or a dedicated secrets manager (e.g. HashiCorp Vault, AWS Secrets Manager).
- Use environment variables or gitignored local files for runtime secrets.
- Never commit `.env` files, JSON files containing keys, or any file with real credentials.
- Rotate any key that has ever appeared in a public git repository.
