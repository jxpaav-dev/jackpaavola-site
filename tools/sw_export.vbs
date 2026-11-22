' usage: cscript sw_export.vbs <in.SLDPRT|SLDASM> <out.stl|png> [<in2> <out2> ...]
Dim sw, doc, i, t, ok
Set sw = CreateObject("SldWorks.Application")
sw.Visible = True
' STL export: binary, fine quality, whole assembly into one file
sw.SetUserPreferenceToggle 72, True      ' swSTLComponentsIntoOneFile
sw.SetUserPreferenceIntegerValue 78, 3   ' swSTLQuality = Custom
sw.SetUserPreferenceDoubleValue 2, 0.00001  ' swSTLDeviation (m) = 0.01 mm
sw.SetUserPreferenceDoubleValue 3, 0.05     ' swSTLAngleTolerance (rad) ~ 3 deg
For i = 0 To WScript.Arguments.Count - 1 Step 2
  t = 1
  If LCase(Right(WScript.Arguments(i), 6)) = "sldasm" Then t = 2
  Set doc = sw.OpenDoc(WScript.Arguments(i), t)
  If doc Is Nothing Then
    WScript.Echo "open failed: " & WScript.Arguments(i)
  Else
    doc.ShowNamedView2 "*Isometric", 7
    doc.ViewZoomtofit2
    ok = doc.SaveAs(WScript.Arguments(i + 1))
    WScript.Echo WScript.Arguments(i + 1) & " -> " & ok
    sw.CloseDoc doc.GetTitle()
  End If
Next
