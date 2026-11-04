# OpsDesk Incident Management

Java 17 / Spring Boot incident dashboard for CI/CD practice.

## Features
- Dashboard counts for total, open, in-progress and resolved incidents
- Search and status filtering
- Create incident and update its status
- REST API, input validation and Actuator health endpoint
- JUnit unit and Spring MVC integration tests

Data is in-memory and resets on restart.

## Run
```bash
mvn clean verify
mvn spring-boot:run
```
Open http://localhost:8080

## API
- GET /api/incidents
- GET /api/incidents/{id}
- POST /api/incidents
- PATCH /api/incidents/{id}/status
- GET /api/statistics
- GET /actuator/health

## Reports
- JUnit: target/surefire-reports/
- JaCoCo: target/site/jacoco/index.html
- OWASP: target/dependency-check-report.html

## Docker
```bash
docker build -t opsdesk:v1 .
docker run --rm -p 8080:8080 opsdesk:v1
```
