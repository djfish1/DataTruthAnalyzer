import DataManager as dm
import ReportGenerator

from collections import OrderedDict
import math
import numpy
import optparse
import os
from scipy.optimize import linear_sum_assignment

class DataTruthAnalyzer(object):
  def __init__(self, trackFile, truthFile):
    self.trackManager = dm.DataManager(trackFile, hasId=True)
    self.truthManager = dm.DataManager(truthFile, hasId=True)
    self.IMPOSSIBLE_SCORE = 1.0E10
    self.NEW_TRACK_SCORE = 10.0
    self.ASSOC_GATE = 2.0
    self.initData()

  def initData(self):
    self.truthAssignments = {}
    self.trackAssignments = {}
    for truthId in self.truthManager.idMapData.keys():
      self.truthAssignments[truthId] = {}
      self.truthAssignments[truthId]['TIME'] = []
      self.truthAssignments[truthId]['TRK_IDS'] = []
    for trkId in self.trackManager.idMapData.keys():
      self.trackAssignments[trkId] = {}
      self.trackAssignments[trkId]['TIME'] = []
      self.trackAssignments[trkId]['TRUTH_IDS'] = []

  def assignTracksToTruth(self):
    uTimes = self.trackManager.getUniqueTimes()
    #print('Unique times:', uTimes)
    self.truthManager.interpolateToTimeAxis(uTimes)
    #print('Interpolated truth data:', self.truthManager.idMapData)
    self.allTimeData = OrderedDict()
    for time in uTimes:
      print '****  Time = ', time, ' *****'
      validTrkIds = []
      validTruthIds = []
      thisTimeTrkData = []
      thisTimeTruthData = []
      for trkId, trkData in self.trackManager.idMapData.items():
        tmpTrkData = self.trackManager.getIndividualDataAtTime(trkData, time)
        if tmpTrkData is not None:
          validTrkIds.append(trkId)
          thisTimeTrkData.append(tmpTrkData)
      #print 'validTrkIds:', validTrkIds
      for truthId, truthData in self.truthManager.idMapData.items():
        # Due to interpolation above, this time has to exist
        tmpTruthData = self.truthManager.getIndividualDataAtTime(truthData, time)
        if not numpy.isnan(tmpTruthData['ID']):
          validTruthIds.append(truthId)
          thisTimeTruthData.append(tmpTruthData)
      #print 'validTruthIds:', validTruthIds
      self._createAssignmentMatrix(thisTimeTrkData, thisTimeTruthData, time)
      numAssociatedTrks = 0
      for iTrk, trkId in enumerate(validTrkIds):
        trkScores = self.assignmentMatrix[0:len(validTruthIds), iTrk]
        numAssociatedTrks += numpy.any(trkScores < self.IMPOSSIBLE_SCORE)
        #print 'Any for trkIdx:', iTrk, 'id:', trkId, trkScores < self.IMPOSSIBLE_SCORE
        #print '  from', trkScores
      #print 'assMatrix:', os.linesep, self.assignmentMatrix
      #print 'Associated Tracks:', numAssociatedTrks
      truthToTrk, trkToTruth = linear_sum_assignment(self.assignmentMatrix)
      truthTrackAssignment = -1*numpy.ones(numpy.shape(validTruthIds), numpy.int)
      trackTruthAssignment = -1*numpy.ones(numpy.shape(validTrkIds), numpy.int)
      numAssignedTrks = 0
      for iTruth, truthId in enumerate(validTruthIds):
        assignedTrk = -1
        if iTruth in truthToTrk:
          numAssignedTrks += 1
          trkIdx = trkToTruth[iTruth]
          assignedTrk = validTrkIds[trkIdx]
          truthTrackAssignment[iTruth] = assignedTrk
          trackTruthAssignment[trkIdx] = truthId
          print 'Truth', truthId, 'assigned to', assignedTrk
        else:
          print 'Truth', truthId, 'not assigned'
        self.truthAssignments[truthId]['TRK_IDS'].append(assignedTrk)
        self.truthAssignments[truthId]['TIME'].append(time)
      for iTrk, trkId in enumerate(validTrkIds):
        assignedTruth = -1
        if iTrk in trkToTruth:
          truthIdx = truthToTrk[iTrk]
          if truthIdx < len(validTruthIds):
            assignedTruth = validTruthIds[truthIdx]
        self.trackAssignments[trkId]['TRUTH_IDS'].append(assignedTruth)
        self.trackAssignments[trkId]['TIME'].append(time)

      thisTimeData = {}
      thisTimeData['numAssociatedTrks'] = numAssociatedTrks
      thisTimeData['numAssignedTrks'] = numAssignedTrks
      thisTimeData['validTrkIds'] = numpy.array(validTrkIds)
      thisTimeData['validTruthIds'] = numpy.array(validTruthIds)
      thisTimeData['truthTrackAssignment'] = numpy.array(truthTrackAssignment)
      thisTimeData['trackTruthAssignment'] = numpy.array(trackTruthAssignment)
      self.allTimeData[time] = thisTimeData
    print('allTimeData:', self.allTimeData)

  def _createAssignmentMatrix(self, thisTimeTrkData, thisTimeTruthData, time):
    numTruths = len(thisTimeTruthData)
    numTracks = len(thisTimeTrkData)
    truthIds = [tmp['ID'] for tmp in thisTimeTruthData]
    trkIds = [tmp['ID'] for tmp in thisTimeTrkData]
    self.assignmentMatrix = numpy.ones((numTruths + numTracks, numTracks)) * self.IMPOSSIBLE_SCORE
    for iTruth, truthId in enumerate(truthIds):
      for iTrk, trkId in enumerate(trkIds):
        truthData = thisTimeTruthData[iTruth]
        trkData = thisTimeTrkData[iTrk]
        self.assignmentMatrix[iTruth, iTrk] = self._getScore(truthData, trkData)
    for iTrk, trkId in enumerate(trkIds):
      self.assignmentMatrix[iTrk + numTruths, iTrk] = self.NEW_TRACK_SCORE
    
  def _getScore(self, truthData, trackData):
    deltaX = truthData['X'] - trackData['X']
    deltaY = truthData['Y'] - trackData['Y']
    score = math.sqrt(deltaX * deltaX + deltaY * deltaY)
    return score if score < self.ASSOC_GATE else self.IMPOSSIBLE_SCORE

if __name__ == '__main__':
  op = optparse.OptionParser()
  op.add_option('--track', type='string', dest='trackFile', help='Track file name')
  op.add_option('--truth', type='string', dest='truthFile', help='Truth file name')
  opts, args = op.parse_args()
  dta = DataTruthAnalyzer(opts.trackFile, opts.truthFile)
  #print('Track data:', dta.trackManager.idMapData)
  #print('Truth data:', dta.truthManager.idMapData)
  dta.assignTracksToTruth()
  rg = ReportGenerator.ReportGenerator(dta, 'testReport')
  rg.generateReport()
