<%

dim ord2
ord2 = 3+555 - 2

if ord2 >= 1000 then
    test = "abc"

    if ord2 >= 1000 then
        test = "abc2"
    elseif ord2 >= 1000 then
        test = "abc3"
    else
        test = "abc4"
    end if
else
    test = "xyz"
	test2 = "oof"
end if

Routine()

val2 = "YA"

Routine()

Sub Routine()
    Response.Write(val2 & "some values:")
	val = "YO"
    val2 = "YAA"
end sub

Function some()
    test = "test"
end function

Function some2(ByRef abc, ByVal def)
    test = "test"
end function

Function some3(abc, def)
    test = "test"
end function


Response.Write("test")
Response.Write(test)
Response.Write(test2)
Response.Write(oof)
Response.Write(val) 'some values:YAsome values:testxyzoofYAA
Response.Write(val2) REM ahaha


%>
<!-- #include file ="include.asp" -->
output
multiline 
<!-- #include file ="include.asp" -->