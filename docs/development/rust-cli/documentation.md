# Documentation Deployment Guide

## Current Setup

The project uses **Read the Docs** for documentation hosting, not GitHub Pages.

## How Read the Docs Works

Read the Docs automatically builds and deploys your documentation when:

1. **Webhook is configured** (automatic when you connect GitHub)
2. **You push to configured branches** (main/develop by default)
3. **Build is triggered** via the webhook

### Setup Steps

1. **Import your project**:
   - Go to https://readthedocs.org/dashboard/import/
   - Click "Import a Project"
   - Select your GitHub repository

2. **Connect GitHub account**:
   - In Read the Docs project settings
   - Go to "Integrations" → "GitHub"
   - Connect your GitHub account
   - Webhook will be automatically configured

3. **Configure build settings**:
   - Read the Docs reads `.readthedocs.yaml` from your repo
   - It uses `mkdocs.yml` for MkDocs configuration
   - Builds happen automatically on every push

4. **Access your docs**:
   - Default URL: `https://<project-name>.readthedocs.io/`
   - Your project: `https://bank-importer.readthedocs.io/`

### What GitHub Actions Does

The `.github/workflows/docs.yml` workflow:
- ✅ **Verifies** documentation builds correctly
- ✅ **Checks** for broken links
- ❌ **Does NOT deploy** (Read the Docs does that)

This is a safety check to catch issues before they reach Read the Docs.

## GitHub Pages (Optional)

If you want GitHub Pages **in addition** to Read the Docs:

1. **Enable GitHub Pages** in repository settings:
   - Settings → Pages
   - Source: "GitHub Actions"

2. **Uncomment the deployment job** in `.github/workflows/docs.yml`

3. **Update mkdocs.yml** if needed:
   ```yaml
   # For GitHub Pages, you might want:
   site_url: https://<username>.github.io/<repo-name>/
   ```

### When to Use GitHub Pages

- ✅ You want documentation on GitHub's infrastructure
- ✅ You want a custom domain
- ✅ You want both Read the Docs AND GitHub Pages

### When to Stick with Read the Docs

- ✅ Better search functionality
- ✅ Automatic versioning
- ✅ PDF/EPUB generation
- ✅ Better for open source projects
- ✅ No GitHub Actions minutes used

## Troubleshooting

### Read the Docs Not Building

1. Check webhook status in Read the Docs project settings
2. Verify `.readthedocs.yaml` is correct
3. Check build logs in Read the Docs dashboard
4. Ensure Python version matches (currently 3.13)

### GitHub Actions Failing

- Check Python version matches
- Verify `docs/requirements.txt` is up to date
- Check for broken links with `mkdocs-linkcheck`

### Both Services

If using both:
- Read the Docs: `https://bank-importer.readthedocs.io/`
- GitHub Pages: `https://<username>.github.io/bank-importer/`

You can link between them or redirect one to the other.

