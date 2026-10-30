# ☕ Brewnook

**An online store for coffee, brewing equipment, and everyday coffee essentials.**

Brewnook is a full-stack e-commerce website developed for **CS 308 – Software Engineering** at **Sabancı University**, Fall 2026–2027.

The project aims to provide a complete online shopping experience, including product browsing, shopping cart management, checkout, order tracking, and real-time customer support.

> **Status:** In development. The features below describe the planned project scope.

## Store Concept

Brewnook offers coffee and equipment for home brewing. The initial catalog contains **32 fictional products across 7 categories**, with prices in **Turkish lira (TRY)**.

| Category | Number of Products |
| --- | ---: |
| Coffee Beans | 6 |
| Ground Coffee | 2 |
| Coffee Grinders | 4 |
| Espresso Machines | 3 |
| Brewing Equipment | 6 |
| Kettles | 3 |
| Accessories | 8 |

Products include information such as name, model, serial or lot number, description, stock quantity, price, warranty status, and distributor details. Coffee products may also include origin, roast date, and expiry date.

All brands, distributors, and contact details in the initial dataset are fictional.

## Planned Features

### Customer Features

- Browse products by category.
- View product details, prices, and available stock.
- Search by product name and description.
- Sort products by price and popularity.
- Add products to the cart, change quantities, and remove items.
- Keep cart contents when signing in.
- Register, sign in, and manage profile and delivery information.
- Complete checkout through a simulated payment system.
- View invoices and receive PDF invoices by email.
- View order history and track delivery status.
- Rate and review delivered products.
- Add products to a wishlist.
- Receive notifications when wishlisted products are discounted.
- Cancel orders while they are processing.
- Request returns for eligible delivered purchases within the 30-day return window.

### Product Management

- Add and remove products and categories.
- Update inventory.
- Approve or reject customer comments.
- Manage delivery records and update order status.
- Access relevant invoices and delivery information.

### Sales Management

- Manage product prices and discounts.
- Notify customers about discounts on wishlisted products.
- View invoices within a selected date range.
- View revenue and profit/loss reports.
- Review return requests and manage refunds.

### Live Customer Support

- Real-time messaging for guests and registered customers.
- A support panel accessible throughout the website.
- A conversation queue and conversation assignment for support agents.
- Image, PDF, and video attachments.
- Authorized access to relevant customer information, including cart contents, orders, delivery status, and wishlist.

## User Roles

| Role | Responsibilities |
| --- | --- |
| Customer | Shopping, checkout, profile management, reviews, wishlist, and order tracking |
| Product Manager | Product and category management, inventory, comment moderation, and deliveries |
| Sales Manager | Pricing, discounts, financial reports, and return approval |
| Support Agent | Live conversations and customer assistance |

Guests can browse products, manage a guest cart, and contact support. Checkout requires signing in.

Role-based access controls will be enforced on the backend.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React + TypeScript |
| Styling | Tailwind CSS |
| UI Components | shadcn/ui |
| Backend | Python + Django |
| REST API | Django REST Framework |
| Database | PostgreSQL |
| Local Database | PostgreSQL running in Docker |
| Hosted Database | Neon |
| Real-Time Communication | Django Channels + WebSockets |
| Channel Layer | Redis |

### Architecture

The application uses a separate React frontend and Django backend.

- **React** provides the storefront and custom management interfaces.
- **Django REST Framework** exposes APIs for accounts, products, carts, orders, and management operations.
- **PostgreSQL** stores persistent application data.
- **Django Channels** handles real-time support conversations.
- **Redis** distributes real-time events between server processes. Chat history is stored in PostgreSQL.

Each developer will work with a separate local PostgreSQL database. The shared Neon database will be used for the deployed application and demonstrations.

For single-process local development, Channels can use an in-memory channel layer. The deployed application will use Redis.

The team will build custom management interfaces for the project.

## Business Rules

- Out-of-stock products remain visible but cannot be added to the cart.
- Stock availability is validated on the backend.
- Order creation and stock reduction must occur atomically to prevent overselling.
- Order items preserve their purchase-time prices for accurate invoicing and refunds.
- Orders can only be cancelled while their status is `processing`.
- Cancelling an order restores its stock.
- Order delivery stages are `processing`, `in-transit`, and `delivered`.
- Customers can rate and review eligible delivered products.
- Ratings appear immediately; written comments require product manager approval.
- Refunds use the amount originally paid, including any discount.
- Returned products are restocked after they are received.
- Financial reports use the recorded product cost. If no cost is provided, the planned fallback is 50% of the sale price.

## Security and Reliability

Planned security and reliability measures include:

- Hashed passwords.
- Server-side authentication and role-based authorization.
- Input validation and file upload restrictions.
- Environment-based configuration for secrets and database credentials.
- Protection of customer, payment, and invoice information.
- No persistent storage of full card numbers or CVV values.
- Database transactions and concurrency controls for inventory operations.

Payments will be simulated for the course project.

## Getting Started

Installation commands, dependency versions, environment variables, and startup instructions will be added as the application infrastructure is implemented.

The planned local development environment requires:

- Python
- Node.js and a package manager
- Docker for PostgreSQL
- Redis when testing communication across multiple server processes

The initial product spreadsheet will serve as the source for development and demo data.

## Development Workflow

The project follows Scrum. Tasks and sprint progress are tracked in Jira, while source code and pull requests are managed through GitHub.

The planned workflow is:

1. Select a Jira issue with defined acceptance criteria.
2. Create a branch for the task.
3. Implement the change and relevant tests.
4. Open a pull request explaining the changes and validation.
5. Obtain at least one teammate's review before merging into `main`.
6. Update the Jira issue after completion.

Suggested branch naming:

- `feature/<issue-key>-short-description`
- `fix/<issue-key>-short-description`
- `docs/<issue-key>-short-description`

Changes affecting shared APIs, database schemas, or common UI components should be coordinated with the team.

## Testing

The testing plan includes unit tests, integration tests, and end-to-end customer journeys.

Priority scenarios include:

- Registration, login, and role permissions.
- Guest cart retention after login.
- Payment approval and rejection.
- Order creation and invoice generation.
- Concurrent purchases of the last available product.
- Review eligibility and comment moderation.
- Order cancellation and stock restoration.
- Returns and refunds using the original purchase price.
- Simultaneous support conversations.
- Attachment type and size validation.

Test commands will be documented once the testing infrastructure is available.

## Project Milestones

| Milestone | Planned Scope |
| --- | --- |
| Initial Development | Project setup, catalog, product details, cart, and authentication |
| Progress Demo | Catalog and cart, search and sorting, stock and order tracking, checkout, invoices, ratings, and comments |
| Final Demo | Management interfaces, wishlist, discounts, returns and refunds, live support, security, and concurrency validation |

Sprint scope may be updated based on implementation progress and TA feedback.

---

Developed by a six-person team for **Sabancı University — CS 308 Software Engineering, Fall 2026–2027**.