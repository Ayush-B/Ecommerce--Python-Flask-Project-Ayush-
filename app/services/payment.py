"""
Asynchronous payment simulation.

Payment succeeds 90 percent of the time and fails 10 percent of the time.
A realistic delay is simulated with asyncio.sleep.
"""

import asyncio
import random


class PaymentService:
    """
    Mock asynchronous payment processor.
    """

    @staticmethod
    async def process_payment(amount_cents: int, user_id: int) -> bool:
        """
        Simulate a payment transaction.

        Returns True on success, False on failure.
        """

        # Simulate network or processor latency
        await asyncio.sleep(1.2)

        # 90 percent chance of success
        return random.random() < 0.9
