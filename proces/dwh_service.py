from typing import cast

import pymssql


class DWHService:
    def __init__(
            self,
            username: str,
            password: str,
            server: str,
            database: str
            ):
            self.username = username
            self.password = password
            self.server = server
            self.database = database
            self._connection = None

    def __enter__(self):
        if not self._connection:
            self._connection = pymssql.connect(
                server=self.server,
                user=self.username,
                password=self.password,
                database=self.database,
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            self._connection.close()

    def close(self):
        if self._connection:
            self._connection.close()

    def hent_medarbejdere(self) -> list[dict]:
        query = f"""
        SELECT *
        FROM {self.database}.[dbo].[statsborgerskab]
        WHERE Land_statsborger NOT IN (
            'Azorerne',
            'Balearerne',
            'Belgien',
            'Bulgarien',
            'Ceuta',
            'Cypern',
            'Danmark',
            'Estland',
            'Finland',
            'Frankrig',
            'Grækenland',
            'Guadeloupe',
            'Guyana',
            'Holland',
            'Nederlandene',
            'Irland',
            'Island',
            'Italien',
            'Kroatien',
            'Letland',
            'Liechtenstein',
            'Litauen',
            'Luxembourg',
            'Madeira',
            'Malta',
            'Martinique',
            'Norge',
            'Polen',
            'Portugal',
            'Reunion',
            'Rumænien',
            'Slovakiet',
            'Slovenien',
            'Spanien',
            'Sverige',
            'Tjekkiet',
            'Tyskland',
            'Ungarn',
            'Østrig',
            'Ålandsøerne',
            'Ukraine'
        )
        """
        
        if self._connection is None:
            raise RuntimeError("DWH connection is not initialized")

        cursor = self._connection.cursor(as_dict=True)
        cursor.execute(query)
        results = cast(list[dict], cursor.fetchall())
        cursor.close()
        
        return results