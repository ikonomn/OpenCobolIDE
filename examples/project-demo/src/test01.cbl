      ******************************************************************
      * Author:
      * Date:
      * Purpose:
      * Tectonics: cobc
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. test01.
       DATA DIVISION.
       FILE SECTION.
       WORKING-STORAGE SECTION.
       copy copybook.
       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           MOVE "HELLO from OpenCobolIDE modern11.6 " TO
           LK-VALUE
           CALL "worker" using LK-VALUE
           STOP RUN.
       END PROGRAM test01.
