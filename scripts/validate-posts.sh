#!/bin/bash
# Validate that all posts follow the template structure

set -euo pipefail

PROJECT_DIR=~/.openclaw/workspace/projects/web-applications/boldlybalance
ERRORS=0

echo "=== POST TEMPLATE VALIDATION ==="
echo ""

for post in "$PROJECT_DIR"/posts/*.html; do
    postname=$(basename "$post")
    errors_in_post=()
    
    # Check for required elements
    if ! grep -q '<span class="tag"' "$post"; then
        errors_in_post+=("Missing: <span class=\"tag\">CATEGORY</span>")
    fi
    
    if ! grep -q '<h1>' "$post"; then
        errors_in_post+=("Missing: <h1>TITLE</h1>")
    fi
    
    if ! grep -q '⏱️' "$post"; then
        errors_in_post+=("Missing: Reading time (⏱️ X min read)")
    fi
    
    if ! grep -q '<p class="excerpt"' "$post"; then
        errors_in_post+=("Missing: <p class=\"excerpt\">...")
    fi
    
    if ! grep -q '<article>' "$post"; then
        errors_in_post+=("Missing: <article> tag")
    fi
    
    if [ ${#errors_in_post[@]} -gt 0 ]; then
        ERRORS=$((ERRORS + 1))
        echo "❌ $postname: Template violations"
        for error in "${errors_in_post[@]}"; do
            echo "   - $error"
        done
        echo ""
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo "✅ All posts follow the template structure correctly"
    exit 0
else
    echo "⚠️  Found $ERRORS posts with template violations"
    echo ""
    echo "REMEDIATION:"
    echo "1. Remove posts that don't follow the template"
    echo "2. Recreate them using: bash scripts/create-post.sh"
    echo ""
    echo "DO NOT create posts manually - always use create-post.sh"
    exit 1
fi
