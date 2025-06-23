' -- -- -- Useful Excel Formulas -- -- -- '

' Extract ", NSW, Australia" from end of address
=LEFT(A1, LEN(A1)-16)

' XLOOKUPs
=IFERROR(XLOOKUP(A1,Sheet2!A:A,Sheet2!B:B),"")
' IFERROR ARG1: XLOOKUP formula
	' XLOOKUP ARG1: Cell value to look up (ID)
	' XLOOKUP ARG2: Lookup array , where to look up the value (ID column)
	' XLOOKUP ARG3: Return array, what to return if the value is found (Value column)
	' XLOOKUP ARG4: What to return if the value is not found (optional) - Not needed because of IFERROR
' IFERROR ARG2: the value to return if the lookup value is not found.

' Get last word in a cell (alternative that leaves "" instead of #VALUE!)
=IFERROR(TRIM(RIGHT(SUBSTITUTE(A2," ",REPT(" ",LEN(A2))),LEN(A2))),"")

' Get last word in a cell - alternative that leaves "" instead of #VALUE and handles 1 word blocks does nothing
=IFERROR(RIGHT(B2,LEN(B2)-FIND("*",SUBSTITUTE(B2," ","*",LEN(B2)-LEN(SUBSTITUTE(B2," ",""))))),IF(COUNTIF(B2," ")=0,"",""))

' Get first word in a cell (alternative that leaves "" instead of #VALUE!)
=IFERROR(TRIM(LEFT(SUBSTITUTE(A2," ",REPT(" ",LEN(A2))),LEN(A2))),"")