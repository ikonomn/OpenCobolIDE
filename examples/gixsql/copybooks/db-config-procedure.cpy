       LOAD-DB-CONFIG.
           MOVE "N" TO DB-CONFIG-OK-FLAG
           DISPLAY "DB_CONFIG_FILE" UPON ENVIRONMENT-NAME
           ACCEPT DB-CONFIG-PATH FROM ENVIRONMENT-VALUE
           IF DB-CONFIG-PATH = SPACES
               IF DB-SQLITE
                   MOVE "../config/application-sqlite.conf"
                       TO DB-CONFIG-PATH
               ELSE
                   IF DB-MARIADB
                       MOVE "../config/application-mariadb.conf"
                           TO DB-CONFIG-PATH
                   ELSE
                       DISPLAY "INVALID DB-FLAG: " DB-FLAG
                       EXIT PARAGRAPH
                   END-IF
               END-IF
           END-IF

           OPEN INPUT DB-CONFIG-FILE
           IF DB-CONFIG-STATUS NOT = "00"
               DISPLAY "CANNOT OPEN CONFIG, STATUS " DB-CONFIG-STATUS
               EXIT PARAGRAPH
           END-IF
           PERFORM UNTIL DB-CONFIG-STATUS = "10"
               READ DB-CONFIG-FILE
                   AT END CONTINUE
                   NOT AT END PERFORM PARSE-DB-CONFIG-LINE
               END-READ
           END-PERFORM
           CLOSE DB-CONFIG-FILE
           DISPLAY "USING CONFIG: " FUNCTION TRIM(DB-CONFIG-PATH)
           DISPLAY "USING DATASOURCE: " FUNCTION TRIM(DATASRC)
           MOVE "Y" TO DB-CONFIG-OK-FLAG.

       PARSE-DB-CONFIG-LINE.
           EVALUATE TRUE
               WHEN DB-CONFIG-LINE(1:8) = "DATASRC="
                   MOVE DB-CONFIG-LINE(9:) TO DATASRC
               WHEN DB-CONFIG-LINE(1:12) = "DATASRC_USR="
                   MOVE DB-CONFIG-LINE(13:) TO DB-USER
               WHEN DB-CONFIG-LINE(1:12) = "DATASRC_PWD="
                   MOVE DB-CONFIG-LINE(13:) TO DB-PASSWORD
           END-EVALUATE.

       END-DB-CONFIG.
           EXIT.
