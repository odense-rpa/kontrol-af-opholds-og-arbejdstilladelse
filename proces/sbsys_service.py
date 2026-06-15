from sbsys.manager import SbsysClientManager
from .models import Medarbejder
from automation_server_client import WorkItemError
import logging

class SbsysService:
    def __init__(self, sbsys: SbsysClientManager):
        self.sbsys = sbsys
    
    async def find_opholdssag_for_tjenstenr(self, medarbejder: Medarbejder) -> dict:
        
        logger = logging.getLogger()
        
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
            return sager[0]
        else:
            raise WorkItemError("Fejl")
        
    async def kontroller_dokumenter_på_sag(self, sags_id: str):
        logger = logging.getLogger()
        
        dokumenter = await self.sbsys.dokumenter.hent_dokumenter_på_sag(sags_id)
        
        for dokument in dokumenter:
            pass
    
    async def kontroller_erindring_på_sag(self, sag: dict) -> str:
        logger = logging.getLogger()
        
        erindringer = await self.sbsys.erindringer.hent_erindringer_på_sag(sag["Id"])
        typer = await self.sbsys.erindringer.hent_erindringstyper()
        
        
        erindring = next(
            (e for e in erindringer if e["SagsTitel"] == "Opholds og arbejdstilladelse" and e["ErAktiv"] == True),
            None
        )
        
        if erindring is None:
            return "Ingen erindring af korrekt type fundet på sagen"
        
        #Tjekker om erindring og sag har samme behandler
        if erindring is not None and erindring["Ansvarlig"]["Id"] == sag["Behandler"]["Id"]:
            return ""
        
        body = {
            "Ansvarlig":{
                "Id": sag["Behandler"]["Id"]
            }  
        }
        
        try:
            await self.sbsys.erindringer.opdater_erindring(erindring["Id"], body)
        except Exception as e:
            return f"Fejl i forsøget på at opdatere erindring med korrekt sagsbehandler, fejl: {e}"
        
        return ""