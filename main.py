import asyncio
import logging
import sys

from automation_server_client import AutomationServer, Workqueue, WorkItemError, Credential, WorkItemStatus
from sbsys.manager import SbsysClientManager
from odk_tools.tracking import Tracker
from odk_tools.reporting import report
from proces.models import Medarbejder
from proces.sbsys_service import SbsysService

sbsys: SbsysClientManager
tracker: Tracker
sbsys_service: SbsysService

procesnavn = "Kontrol af opholds- og arbejdstilladelse"


async def populate_queue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from populate workqueue!")


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from process workqueue!")

    async with sbsys:
        for item in workqueue:
            with item:
                try:
                    manuel_besked = ""
                    
                    medarbejder = Medarbejder.model_validate(item.data)

                    sag = await sbsys_service.find_opholdssag_for_tjenstenr(medarbejder)
                    
                    manuel_besked = await sbsys_service.kontroller_erindring_på_sag(sag)
                    
                    if manuel_besked != "":
                        report(
                            "kontrol-af-opholds-og-arbejdstilladelse",
                            "Manuel",
                            {
                                "Cpr": medarbejder.cpr,
                                "Navn": medarbejder.navn,
                                "Årsag": manuel_besked                                
                            }
                        )
               
                except WorkItemError as e:
                    # A WorkItemError represents a soft error that indicates the item should be passed to manual processing or a business logic fault
                    logger.error(f"Error processing item: {medarbejder}. Error: {e}")
                    item.fail(str(e))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    
    ats = AutomationServer.from_environment()
    workqueue = ats.workqueue()

    # Initialize external systems for automation here..
    sbsys_credential = Credential.get_credential("P-sag - produktion")
    tracking_credential = Credential.get_credential("Odense SQL Server")
    if tracking_credential.username is None or tracking_credential.password is None:
        raise ValueError("Tracking credential is missing username or password")
    if sbsys_credential.username is None or sbsys_credential.password is None:
        raise ValueError("SBSYS credential is missing username or password")

    sbsys = SbsysClientManager(
        sbsys_credential.data["base_url"],
        sbsys_credential.data["token_url"],
        sbsys_credential.data["client_id"],
        sbsys_credential.data["client_secret"],
        sbsys_credential.username,
        sbsys_credential.password
    )
    
    tracker = Tracker(
        username=tracking_credential.username,
        password=tracking_credential.password
    )
    
    sbsys_service = SbsysService(
        sbsys
    )

    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        asyncio.run(populate_queue(workqueue))
        exit(0)

    # Process workqueue
    asyncio.run(process_workqueue(workqueue))
