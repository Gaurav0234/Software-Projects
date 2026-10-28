# Expense Tracker — Spring Boot Microservices

A backend-focused expense tracking project built as separate Java/Spring Boot services with MySQL persistence and Apache Kafka for event-driven communication. A Python/Flask service experiments with using an LLM to interpret bank-related SMS messages and publish extracted expense data.

> **Project status:** Portfolio / learning project. The repository has not been validated here with a full end-to-end run. Review the configuration notes below before running it.

## Architecture

| Service | Stack | Responsibility |
|---|---|---|
| **Auth Service** | Java 21, Spring Boot, Spring Security, JWT, MySQL, Kafka | Signup/login, issuing access and refresh tokens, and publishing user-information events |
| **userservice** | Java 21, Spring Boot, Spring Data JPA, MySQL, Kafka | Consumes user events and exposes user lookup/create-update endpoints |
| **Expense service** | Java 21, Spring Boot, Spring Data JPA, MySQL, Kafka | Persists expense records and exposes expense endpoints; consumes expense events |
| **DSSERVICE** | Python, Flask, Kafka, LangChain model integration | Accepts message text, checks whether it resembles a bank SMS, attempts structured expense extraction, and publishes the result |

### Event flow

1. A client signs up through the Auth Service.
2. The Auth Service saves the account and publishes a user-information event to Kafka on the `user_service` topic.
3. The userservice consumes that event and creates or updates its local user record.
4. DSSERVICE accepts a message at `POST /v1/ds/message`, checks for bank-related keywords, and attempts to extract expense fields.
5. DSSERVICE publishes the result to the Kafka `my-topic` topic, which the Expense service consumes and persists.

The Java services use separate MySQL database names by default: `authservice`, `userservice`, and `expenseservice`.

## Technology stack

- Java 21 and Spring Boot 3.2.x
- Spring Security and JWT
- Spring Data JPA / Hibernate
- MySQL
- Apache Kafka
- Gradle Wrapper
- Python and Flask
- LangChain model integration

## Repository layout

```text
Expense Tracker-Spring Boot/
├── Auth Service/
│   ├── app/src/main/java/       # Authentication API and business logic
│   ├── app/src/main/resources/  # Service configuration
│   ├── app/src/test/            # Tests
│   ├── app/build.gradle
│   └── gradlew / gradlew.bat
├── userservice/
│   ├── src/main/java/
│   ├── src/main/resources/
│   ├── src/test/
│   ├── build.gradle
│   └── gradlew / gradlew.bat
├── Expense service/
│   ├── src/main/java/
│   ├── src/main/resources/
│   ├── src/test/
│   ├── build.gradle
│   └── gradlew / gradlew.bat
└── DSSERVICE/
    └── src/app/                 # Flask app, LLM service and Kafka producer
```

## Prerequisites

Install and configure the following before starting the services:

- JDK 21
- MySQL
- Apache Kafka
- Python 3
- Python packages imported by DSSERVICE, including Flask, `kafka-python`, `python-dotenv`, and the LangChain integrations used by the code

**Reproducibility note:** DSSERVICE currently has no `requirements.txt`, so Python dependency installation is not yet fully reproducible.

## Configuration and security

**Do not commit real passwords, API keys, or signing secrets.** Supply secrets through environment variables, IDE run configurations, or a deployment environment.

The current checked-in code contains hardcoded MySQL credentials and a JWT signing secret. Treat committed secrets as exposed and replace them; removing a value from the latest file does not remove it from Git history.

The JDBC URLs support these environment-variable placeholders:

| Variable | Purpose | Current default |
|---|---|---|
| `MYSQL_HOST` | MySQL hostname | `localhost` for Auth and Expense; `mysql` for userservice |
| `MYSQL_PORT` | MySQL port | `3306` |
| `MYSQL_DB` | Database name | Service-specific |
| `MYSQL_USERNAME` | Recommended environment variable for DB username | Not currently wired into the checked-in properties |
| `MYSQL_PASSWORD` | Recommended environment variable for DB password | Not currently wired into the checked-in properties |
| `KAFKA_HOST` | Kafka hostname | `localhost` in Auth and Expense configuration; verify userservice configuration |
| `KAFKA_PORT` | Kafka port | `9092` |
| `JWT_SECRET` | Recommended environment variable for the JWT signing secret after the code is updated | Not currently wired into `JwtService` |

The checked-in `application.properties` files currently hardcode the MySQL username/password, and Auth Service currently hardcodes its JWT secret. The environment-variable names above describe the recommended approach; update the properties and Java code before relying on them.

DSSERVICE's LLM configuration also needs attention: its current code reads `OPENAI_API_KEY` and passes it to `ChatMistralAI`. Align the environment-variable name and credential with the model provider actually being used.

## API endpoints currently defined in the code

Endpoints are relative to each service's host and port. Confirm request DTOs, authentication requirements, and error responses in the source before integrating a client.

### Auth Service — port 9898

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/v1/signup` | Register a user and return tokens |
| `POST` | `/auth/v1/login` | Authenticate and return tokens |
| `POST` | `/auth/v1/refreshToken` | Exchange a refresh token for a new access token |

### userservice — port 9810

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/user/v1/createUpdate` | Create or update a user record |
| `GET` | `/user/v1/getUser/{userId}` | Retrieve a user by ID |

### Expense service — port 9820

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/expense/v1/` | Retrieve expenses for a user; verify the user-ID query parameter binding |
| `POST` | `/addExpense` | Create an expense; reads the user ID from the `X-User-Id` header |

**API note:** The Expense controller's parameter annotations should be verified/fixed before relying on these endpoints. The POST handler should explicitly bind a JSON request body if JSON is the intended request format.

### DSSERVICE — port 8000

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Simple service health response |
| `POST` | `/v1/ds/message` | Submit message text for classification/extraction |

## Running the Java services

Each Java service is an independent Gradle project. Configure MySQL and Kafka first, set credentials safely, and make sure each service points to the correct hostnames for your environment.

On Windows PowerShell, run each service in a separate terminal. Example for Auth Service:

```powershell
cd "Expense Tracker-Spring Boot\Auth Service"
.\gradlew.bat test
.\gradlew.bat bootRun
```

Run the wrapper from `userservice` and `Expense service` directories in the same way:

```powershell
.\gradlew.bat test
.\gradlew.bat bootRun
```

The Auth Service Gradle project uses the nested `app` subproject; if the default task does not launch it as expected, use the appropriate task for `app`.

### Important database warning

The current JPA configuration includes `spring.jpa.hibernate.ddl-auto=create` in all three Java services. This can recreate schema objects and risk data loss on startup. Change it to an appropriate development or migration strategy before using a database containing data you need to keep. The Expense service also has a conflicting Hibernate DDL setting that should be reconciled.

## Running DSSERVICE

Create and activate a Python virtual environment, install the packages used by the code, configure the LLM provider credential, and configure the Kafka bootstrap address before starting Flask.

The Kafka bootstrap address is currently hardcoded in `DSSERVICE/src/app/__init__.py`; make it configurable for your environment before running the service on a different machine. Disable Flask debug mode outside local development.

## Tests

Each Java service has a test source directory, but the current tests are basic and should not be taken as proof of end-to-end correctness. Add focused tests for authentication, JWT validation, expense request binding, Kafka event handling, and database behavior. DSSERVICE should also have tests for message classification, extraction failures, and Kafka publishing.

## Known limitations and next steps

- Replace hardcoded database credentials and the JWT secret with environment-driven configuration.
- Change `ddl-auto=create` to a safer schema strategy and resolve conflicting Hibernate DDL settings.
- Make DSSERVICE's Kafka address configurable and disable Flask debug mode outside local development.
- Align the LLM API-key variable with the actual model provider.
- Add a Python dependency file and automated tests.
- Correct and test the Expense controller's request parameter/body binding.
- Improve error handling and observability across Kafka consumers and HTTP endpoints.
- Add a reproducible local setup, such as Docker Compose, once service configuration is environment-driven.

## Project purpose

This project is a practical exercise in backend development with Spring Boot, REST APIs, authentication, persistence, and asynchronous communication through Kafka, with an experimental Python/LLM component for expense extraction. It demonstrates the architecture and implementation work while documenting areas for further hardening.
