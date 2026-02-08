# Applications

This directory contains standalone applications.

## Structure

```
apps/
├── web-dashboard/    # Web-based control panel
├── admin-panel/      # Admin interface
└── customer-portal/  # Customer self-service
```

## Guidelines

- Each app should be self-contained
- Include README.md in each app directory
- Document dependencies and setup
- Include Dockerfile if applicable

## Adding New Apps

1. Create new directory: `apps/your-app/`
2. Add README.md with setup instructions
3. Add to main README.md
4. Update CI/CD if needed
