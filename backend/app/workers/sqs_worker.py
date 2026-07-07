import asyncio
import logging
from app.services.sqs_consumer import poll_messages
from app.services.anomaly_detector import detect_anomaly
from app.database import SessionLocal
from app.models.incident import Incident

logger = logging.getLogger(__name__)

async def run_worker():
    logger.info("SQS worker started")
    while True:
        try:
            messages = poll_messages()
            if messages:
                db = SessionLocal()
                try:
                    for msg in messages:
                        anomaly = detect_anomaly(
                            server_name=msg["server_name"],
                            cpu_percent=msg["cpu_percent"],
                            memory_percent=msg["memory_percent"],
                        )
                        if anomaly:
                            incident = Incident(**anomaly)
                            db.add(incident)
                            logger.info(f"Incident created: {anomaly['server_name']} - {anomaly['severity']}")
                    db.commit()
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Worker error: {e}")
        await asyncio.sleep(5)