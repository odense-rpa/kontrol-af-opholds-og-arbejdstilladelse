from sbsys.manager import SbsysClientManager
from .models import Medarbejder
from automation_server_client import WorkItemError
import logging
from datetime import datetime, timezone, timedelta

class SbsysService:
    def __init__(self, sbsys: SbsysClientManager):
        self.sbsys = sbsys
    
    async def find_opholdssag_for_tjenstenr(self, medarbejder: Medarbejder) -> dict|None:
        logger = logging.getLogger()
        
        logger.info("Søger efter arbejds- og opholdssag for medarbejder på tjenstenr")
        sager = await self.sbsys.sager.søg_sager(
            {
                "SagsStatusIds": [
                    6
                ],
                "PrimaerPerson":{
                    "CprNummer":medarbejder.cpr
                },
                "SagsSkabeloner":[
                    "3127"
                ],
                "SagsFelter": [
                    {
                        "Noegle": "EmploymentId",
                        "Vaerdi": str(medarbejder.tjensetenr)
                    }
                ]
            }
        )
        
        if len(sager) == 1:
            logger.info("Sag fundet")
            return sager[0]
        else:
            logger.info("Sag ikke fundet, sender medarbejder til manuel")
            return None
        
    async def kontroller_dokumenter_på_sag(self, sags_id: str):
        logger = logging.getLogger()
        
        dokumenter = await self.sbsys.dokumenter.hent_dokumenter_på_sag(sags_id)
        
        for dokument in dokumenter:
            pass
    
    async def kontroller_erindring_på_sag(self, sag: dict) -> str:
        logger = logging.getLogger()
        
        logger.info("Henter erindringer på sag")
        erindringer = await self.sbsys.erindringer.hent_erindringer_på_sag(sag["Id"])
       
        matchende_erindringer = [
            e for e in erindringer if "opholds- og arbejdstilladelse" in e["Navn"].lower() and datetime.fromisoformat(e["Deadline"]) > datetime.now(timezone.utc) + timedelta(days=14)
        ]

        if len(matchende_erindringer) == 0:
            logger.info("Erindring ikke fundet, sender til manuel")
            return "Ingen 'arbejds- og opholdserindring' fundet på sagen"

        if len(matchende_erindringer) > 1:
            logger.info("Mere end en erindring fundet, sender til manuk")
            return "Mere end én 'arbejds- og opholdserindring' erindring fundet på sagen"

        erindring = matchende_erindringer[0]
        
        #Tjekker om erindring og sag har samme behandler
        if erindring is not None and erindring["Ansvarlig"]["Id"] == sag["Behandler"]["Id"]:
            logger.info("Erindring fundet, og sagsbehandler matcher på erindring og sag, alt godt")
            return ""
        
        body = {
            "Ansvarlig":{
                "Id": sag["Behandler"]["Id"]
            }  
        }
        
        try:
            logger.info("Erindring fundet, men sagsbehandler matcher ikke sagen, opdatere erindring med korrekt sagsbehandler")
            await self.sbsys.erindringer.opdater_erindring(erindring["Id"], body)
        except Exception as e:
            logger.error("Fejl kunne ikke opdatere erindring")
            return f"Fejl i forsøget på at opdatere erindring med korrekt sagsbehandler, fejl: {e}"
        
        logger.info("Erindring opdateret, alt godt")
        return ""