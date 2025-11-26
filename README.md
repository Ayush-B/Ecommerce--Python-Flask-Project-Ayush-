# Ecommerce System
This repository is the outline for a small ecommerce application I am building to understand how a complete web system works. My plan is to use Flask for the backend, SQLAlchemy with MySQL for the database, and Semantic UI for the frontend. I want the project to feel realistic enough to learn from, but simple enough that I can follow every part of it as I build.

The goal of the system is to support user registration and login, product browsing with categories and search, a session-based cart, and a checkout process. I will be adding an asynchronous payment simulation so I can practice using async and await inside Flask. Users will eventually be able to see their past orders and update their shipping information.

I also plan to build an admin dashboard so I can learn how user roles, permissions, and data management work in a real application. The admin will be able to manage products, users, and orders. Every admin action will be written to an activity log, and I want to include a streaming view of this log using a generator so I can practice Python’s iterator techniques in a practical setting.

Throughout the project I am aiming to use important Python concepts in natural ways. This includes object-oriented models with inheritance and abstract base classes, list comprehensions for filtering, decorators for authentication checks, context managers for safe operations, async functions for simulated tasks, and utility modules for datetime and price handling.
