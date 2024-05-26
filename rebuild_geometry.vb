Imports System
Imports NXOpen
Imports NXOpen.UF
Imports System.Collections.Generic


Module NXJournal
Sub Main (ByVal args() As String) 

Dim theSession As NXOpen.Session = NXOpen.Session.GetSession()
Dim workPart As NXOpen.Part = theSession.Parts.Work

Dim displayPart As NXOpen.Part = theSession.Parts.Display

Dim basePart1 As NXOpen.BasePart = Nothing
basePart1 = theSession.Parts.BaseWork

' ----------------------------------------------
'   Menu: File->Open...
' ----------------------------------------------
' Potential journal callback detected. Pausing journal.
' Journal callback ended. Unpausing
Dim basePart2 As NXOpen.BasePart = Nothing
Dim partLoadStatus1 As NXOpen.PartLoadStatus = Nothing
basePart2 = theSession.Parts.OpenActiveDisplay("parametric_wing.prt", NXOpen.DisplayPartOption.AllowAdditional, partLoadStatus1)

partLoadStatus1.Dispose()
Dim basePart3 As NXOpen.BasePart = Nothing
basePart3 = theSession.Parts.BaseWork

Dim basePart4 As NXOpen.BasePart = Nothing
basePart4 = theSession.Parts.BaseWork

' ----------------------------------------------
'   Menu: Tools->Expressions...
' ----------------------------------------------
theSession.Preferences.Modeling.UpdatePending = False

Dim markId1 As NXOpen.Session.UndoMarkId = Nothing
markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Start")

theSession.SetUndoMarkName(markId1, "Expressions Dialog")

Dim markId2 As NXOpen.Session.UndoMarkId = Nothing
markId2 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Import Expressions")

Dim expModified1 As Boolean = Nothing
Dim errorMessages1() As String
basePart4.Expressions.ImportFromFile("group1.exp", NXOpen.ExpressionCollection.ImportMode.Replace, expModified1, errorMessages1)

Dim markId3 As NXOpen.Session.UndoMarkId = Nothing
markId3 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Expressions")

theSession.DeleteUndoMark(markId3, Nothing)

Dim markId4 As NXOpen.Session.UndoMarkId = Nothing
markId4 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Expressions")

Dim markId5 As NXOpen.Session.UndoMarkId = Nothing
markId5 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Make Up to Date")

Dim markId6 As NXOpen.Session.UndoMarkId = Nothing
markId6 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "NX update")

Dim nErrs1 As Integer = Nothing
nErrs1 = theSession.UpdateManager.DoUpdate(markId6)

theSession.DeleteUndoMark(markId6, "NX update")

theSession.DeleteUndoMark(markId5, Nothing)

theSession.DeleteUndoMark(markId4, Nothing)

theSession.SetUndoMarkName(markId1, "Expressions")

theSession.DeleteUndoMark(markId2, Nothing)

' ----------------------------------------------
'   Menu: Tools->Journal->Stop Recording
' ----------------------------------------------

Main2()
End Sub

Sub Main2()
 
       Dim theSession As Session = Session.GetSession()
       Dim ufs As UFSession = UFSession.GetUFSession()
       Dim workPart As Part = theSession.Parts.Work
       Dim displayPart As Part = theSession.Parts.Display
       Dim lw As ListingWindow = theSession.ListingWindow
       Dim mySelectedObjects() As NXObject

       Dim exportFileName As String = Nothing
       Dim i As Integer = 0
 
       lw.Open()

        Dim mySolids As List(Of Body) = New List(Of Body)
        Dim tagList As New List(Of Tag)
         
        'workPart.Bodies collection contains both solid and sheet bodies
        'filter out solid bodies and add them to the list
        For Each solid As Body In workPart.Bodies
            If solid.IsSolidBody Then
                mySolids.Add(solid)
            tagList.Add(solid.Tag)
            End If
        Next
 
 
       'return the full path of the work part
       exportFileName = workPart.FullPath
       'trim off ".prt" and add ".x_t"
       exportFileName = exportFileName.Remove(exportFileName.Length - 4, 4) + ".x_t"
       'if this file already exists, delete it
       If My.Computer.FileSystem.FileExists(exportFileName) Then
           My.Computer.FileSystem.DeleteFile(exportFileName)
       End If
 
       Try
           ufs.Ps.ExportData(tagList.ToArray, exportFileName)
       Catch ex As NXException
           lw.WriteLine("*** ERROR ***")
           lw.WriteLine(ex.ErrorCode.ToString & " : " & ex.Message)
       End Try
 
       lw.Close()
 
    End Sub
End Module