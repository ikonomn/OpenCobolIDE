      ******************************************************************
      * Minimal GixSQL example for SQLite and MariaDB.
      * Change "00" to "01" below to select the MariaDB profile.
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. DATABASE-TEST.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT DB-CONFIG-FILE ASSIGN TO DYNAMIC DB-CONFIG-PATH
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS DB-CONFIG-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD DB-CONFIG-FILE.
       01 DB-CONFIG-LINE PIC X(1024).

       WORKING-STORAGE SECTION.
       01 DB-FLAG PIC X(2) VALUE "00".
          88 DB-SQLITE  VALUE "00".
          88 DB-MARIADB VALUE "01".
       01 DB-CONFIG-PATH   PIC X(512) VALUE SPACES.
       01 DB-CONFIG-STATUS PIC XX VALUE SPACES.
       01 DB-CONFIG-OK-FLAG PIC X VALUE "N".
          88 DB-CONFIG-OK VALUE "Y".
       01 DATASRC     PIC X(512) VALUE SPACES.
       01 DB-USER     PIC X(64) VALUE SPACES.
       01 DB-PASSWORD PIC X(64) VALUE SPACES.
       01 TEST-VALUE  PIC 9(9) VALUE ZERO.

       EXEC SQL INCLUDE SQLCA END-EXEC.

       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
      *    Choose the default profile: "00" is SQLite, "01" is MariaDB.
           MOVE "00" TO DB-FLAG
           PERFORM LOAD-DB-CONFIG
           IF NOT DB-CONFIG-OK
               MOVE 2 TO RETURN-CODE
               STOP RUN
           END-IF

           EXEC SQL
               CONNECT :DB-USER IDENTIFIED BY :DB-PASSWORD
                   USING :DATASRC
           END-EXEC
           IF SQLCODE NOT = ZERO
               PERFORM REPORT-SQL-ERROR
               STOP RUN
           END-IF

      *    Keep the query simple: this example only verifies the connection.
           EXEC SQL SELECT 1 INTO :TEST-VALUE END-EXEC
           IF SQLCODE = ZERO
               DISPLAY "DATABASE CONNECTION OK"
               DISPLAY "SELECT RESULT: " TEST-VALUE
           ELSE
               PERFORM REPORT-SQL-ERROR
           END-IF

           EXEC SQL CONNECT RESET END-EXEC
           STOP RUN.

       REPORT-SQL-ERROR.
           DISPLAY "SQLCODE=" SQLCODE " SQLSTATE=" SQLSTATE
           IF SQLERRML > ZERO
               DISPLAY SQLERRMC(1:SQLERRML)
           END-IF
           MOVE 1 TO RETURN-CODE.

       COPY "db-config-procedure.cpy".
