import asyncio
import json
import logging
from typing import AsyncGenerator

logger = logging.getLogger("meety")

class Notifier:
    """
    Simple in-memory pub/sub for Server-Sent Events (SSE).
    Allows the webhook handler to notify the Web UI.
    """
    def __init__(self):
        self.connections: list[asyncio.Queue] = []

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe a new client to the event stream."""
        queue = asyncio.Queue()
        self.connections.append(queue)
        logger.debug(f"New SSE client connected. Total: {len(self.connections)}")
        try:
            while True:
                message = await queue.get()
                yield f"data: {message}\n\n"
        finally:
            self.connections.remove(queue)
            logger.debug(f"SSE client disconnected. Total: {len(self.connections)}")

    async def broadcast(self, event_type: str, data: dict):
        """Broadcast an event to all connected clients."""
        if not self.connections:
            return

        message = json.dumps({
            "event": event_type,
            "data": data
        })
        
        logger.debug(f"Broadcasting {event_type} to {len(self.connections)} clients")
        for queue in self.connections:
            await queue.put(message)

# Global instance
notifier = Notifier()
