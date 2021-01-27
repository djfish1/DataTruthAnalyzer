import collections
import matplotlib as mat
import matplotlib.pyplot as plt
import numpy
import os

class ReportGenerator(object):

  def __init__(self, dataTruthAnalyzer, baseName, plotFile):
    self.dta = dataTruthAnalyzer
    self.baseName = baseName
    self.outDir = self.baseName + 'Plots'
    os.makedirs(self.outDir, exist_ok=True)
    self._setupPlotDefaults()
    self.plotFile = plotFile
    self._setupPlots()

  def _setupPlots(self):
    self.plotDict = collections.OrderedDict()
    with open(self.plotFile, 'r') as pf:
      for line in pf.readlines():
        print('Line:', line)
        splitLine = line.strip().split(':')
        cat = splitLine[0]
        x = splitLine[1]
        y = splitLine[2]
        plotList = self.plotDict.get(cat, [])
        plotList.append((x, y))
        self.plotDict[cat] = plotList

    print(self.plotDict)

  def _setupPlotDefaults(self):
    p = mat.rcParams
    p.update({'xtick.labelsize': 'large'})
    p.update({'ytick.labelsize': 'large'})
    p.update({'axes.labelsize': 'large'})
    p.update({'axes.linewidth': 2.5})
    p.update({'axes.titlesize': 'x-large'})
    p.update({'axes.titleweight': 'bold'})
    p.update({'axes.xmargin': 0.01})
    p.update({'axes.ymargin': 0.01})
    p.update({'lines.linewidth': 2.5})
    p.update({'lines.markersize': 8.0})
    p.update({'markers.fillstyle': 'full'})
    p.update({'legend.markerscale': 2.0})
    p.update({'legend.numpoints': 1})
    self.defaultLineCycler = plt.cycler('color', ('#0000dd', '#dd0000', '#00dd00', '#ddaa00', '#000000', '#00dddd'))

  def generateReport(self):
    with open(self.baseName+'.tex', 'w') as self.latexFile:
      self._makeHeader()
      self._makeSiapMetrics(self.dta.allTimeData)
      self._makeTruthSummary(self.dta.truthManager)
      self._makeTruthAssignmentSummary()
      self._makeTrackAssignmentSummary()
      self._makeFooter()
    os.system(' '.join(('pdflatex', self.baseName+'.tex', '>', '/dev/null')))

  def write(self, *args):
    strToWrite = ' '.join([str(arg) for arg in args])
    self.latexFile.write(strToWrite + os.linesep)

  def _makeHeader(self):
    self.write('\\documentclass[12pt]{article}')
    self.write('\\usepackage{amsmath}' + os.linesep)
    self.write('\\usepackage{graphicx}' + os.linesep)
    self.write('\\textwidth=7.0in' + os.linesep)
    self.write('\\evensidemargin=-0.25in' + os.linesep)
    self.write('\\oddsidemargin=-0.25in' + os.linesep)
    self.write(''.join(('\\title{', self.baseName, '}')))
    self.write(''.join(('\\author{', os.getenv('USER'), '}')))
    self.write('\\begin{document}')
    self.write('\\begin{abstract}')
    self.write('This is an automated report.')
    self.write('\\end{abstract}')
    self.write('\\maketitle')

  def _makeFooter(self):
    self.write('\\end{document}')

  def _makeSiapMetrics(self, allTimeData):
    self.write('\\pagebreak')
    self.write('\\section{Single Integrated Air Picture (SIAP) Metrics}')
    
    # Grab values out of the allTimeData that we need for the different calculation.
    times = numpy.array([k for k in allTimeData.keys()])
    numAssigned = numpy.array([d['numAssignedTrks'] for d in allTimeData.values()], float)
    numAssoc = numpy.array([d['numAssociatedTrks'] for d in allTimeData.values()], float)
    numTruth = numpy.array([len(d['validTruthIds']) for d in allTimeData.values()], float)
    numTrksTotal = numpy.array([len(d['validTrkIds']) for d in allTimeData.values()], float)
    # Completeness
    self.write('\\subsection{Completeness}')
    self.write('Completeness is the ratio of the number of tracks assigned to truth objects ("good tracks") to',
        'the total number of valid truth objects.')
    self.write('\\begin{eqnarray*}')
    self.write('C_{t} = \\frac{N_{trk, assigned}^{t}}{N_{tgt}^{t}} \\\\')
    self.write('C = \\frac{\\sum_{t}^{}{N_{trk, assigned}^{t}}}{\\sum_{t}^{}{N_{tgt}^{t}}}')
    self.write('\\end{eqnarray*}')
    #print('numAssigned', numAssigned)
    #print('numTruth', numTruth)
    completeness = sum(numAssigned) / sum(numTruth)
    self.write('The overall completess is:', '{0:.3f}\\%.'.format(100.0*completeness))
    fig, ax = self._getSingleAxisFigure(xlabel='Time', ylabel='Completeness', title='Completeness Over Time')
    print('times:', times, 'shape:', numpy.shape(times))
    ax.plot(times, 100.0 * numAssigned / numTruth, 'bo')
    ax.plot(times, 100.0 * numpy.ones(numpy.shape(times)), 'g:')
    ax.plot(times, numpy.zeros(numpy.shape(times)), 'r:')
    ax.set(ylim=(-5., 105.))
    self._addFigures([fig], ['siapCompleteness.pdf'], 1)

    # False track ratio
    self.write('\\subsection{False Track Ratio}')
    self.write('False track ratio is the ratio of the number of tracks not associated with truth objects ("false tracks") to',
        'the total number of valid tracks.')
    self.write('Note that we use count associated tracks here as good, even if they are not ultimately assigned to a truth object.')
    self.write('In this way, false track ratio does not penalize for track duals (multiple tracks on the same target).')
    self.write('\\begin{eqnarray*}')
    self.write('FTR_{t} = \\frac{N_{trk, total}^{t} - N_{trk, assoc}^{t}}{N_{trk, total}^{t}} \\\\')
    self.write('FTR = \\frac{\\sum_{t}^{}{N_{trk, total}^{t} - N_{trk, assoc}^{t}}}{\\sum_{t}^{}{N_{trk, total}^{t}}}')
    self.write('\\end{eqnarray*}')
    #print('numAssoc', numAssoc)
    #print('numTotal', numTrksTotal)
    ftr = sum(numTrksTotal - numAssoc) / sum(numTrksTotal)
    self.write('The overall false track ratio is:', '{0:.3f}\\%.'.format(100.0*ftr))
    fig, ax = self._getSingleAxisFigure(xlabel='Time', ylabel='FTR', title='False Track Ratio Over Time')
    ax.plot(times, 100.0 * (numTrksTotal - numAssoc) / numTrksTotal, 'bo')
    ax.plot(times, 100.0 * numpy.ones(numpy.shape(times)), 'g:')
    ax.plot(times, numpy.zeros(numpy.shape(times)), 'r:')
    ax.set(ylim=(-5., 105.))
    self._addFigures([fig], ['siapFalseTrackRatio.pdf'], 1)

    # Ambiguity
    self.write('\\subsection{Ambiguity}')
    self.write('Ambiguity is the ratio of associated tracks to assigned tracks.')
    self.write('An ambiguity score of 1 represents a completely unambiguous air picture (no track duals).')
    self.write('\\begin{eqnarray*}')
    self.write('A{t} = \\frac{N_{trk, assoc}^{t}}{N_{trk, assigned}^{t}} \\\\')
    self.write('A = \\frac{\\sum_{t}^{}{N_{trk, assoc}^{t}}}{\\sum_{t}^{}{N_{trk, assigned}^{t}}}')
    self.write('\\end{eqnarray*}')
    #print('numAssoc', numAssoc)
    #print('numAssigned', numAssigned)
    amb = sum(numAssoc) / sum(numAssigned)
    self.write('The overall ambiguity is:', '{0:.3f}.'.format(amb))
    fig, ax = self._getSingleAxisFigure(xlabel='Time', ylabel='Ambiguity', title='Ambiguity Over Time')
    ax.plot(times, numAssoc / numAssigned, 'bo')
    ax.plot(times, 1.0 * numpy.ones(numpy.shape(times)), 'g:')
    ax.plot(times, numpy.zeros(numpy.shape(times)), 'r:')
    self._addFigures([fig], ['siapAmbiguity.pdf'], 1)

  def _makeTruthSummary(self, truthManager):
    # Geometry for all truth objects together
    self.write('\\pagebreak')
    self.write('\\section{Truth Summary}')
    self.write('\\subsection{Overall Truth Geometry}')
    fig, ax = self._getSingleAxisFigure(xlabel='X', ylabel='Y', title='Overall Geometry', prop_cycle=self.defaultLineCycler)
    for truthId, truthData in truthManager.idMapData.items():
      xAxis, yAxis = ('X', 'Y')
      ax.plot(truthData[xAxis], truthData[yAxis], '-', label=str(truthId))
      log = numpy.logical_not(numpy.logical_or(numpy.isnan(truthData[xAxis]), numpy.isnan(truthData[yAxis])))
      print(log)
      idx = numpy.squeeze(numpy.where(log))
      #print('idx:', idx)
      ax.plot(truthData[xAxis][idx[0]], truthData[yAxis][idx[0]], 'go', label=None)
      ax.plot(truthData[xAxis][idx[-1]], truthData[yAxis][idx[-1]], 'ro', label=None)
    ax.legend()
    self._addFigures([fig], ['truthOverallGeometry.pdf'], 1)
    for truthId, truthData in truthManager.idMapData.items():
      self.write('\\subsection{Summary for truth: ' + str(truthId) + '}')
      figs = []
      names = []
      for plotDims in self.plotDict['TRUTH']:
        xAxis = self.dta.truthManager._timeField if plotDims[0] == 'T' else plotDims[0]
        yAxis = self.dta.truthManager._timeField if plotDims[1] == 'T' else plotDims[1]
        fig, ax = self._getSingleAxisFigure(xlabel=xAxis,
          ylabel=yAxis,
          title='{0:s} vs {1:s} for truth {2:s}'.format(xAxis, yAxis, str(truthId)))
        figs.append(fig)
        names.append('truth{2:d}_{0:s}vs{1:s}.pdf'.format(xAxis, yAxis, truthId))
        ax.plot(truthData[xAxis], truthData[yAxis], 'b-')
      self._addFigures(figs, names, 2)

  def _makeTrackAssignmentSummary(self):
    self.write('\\pagebreak')
    self.write('\\section{Track Assignments}')
    times = self.dta.allTimeData.keys()
    allTrackIds = self.dta.trackManager.idMapData.keys()
    for iTrk, trkId in enumerate(allTrackIds):
      self.write('\\subsection{Track', trkId, 'Assignments}')
      #print('Looking at track', trkId)
      truthAssignments = self.dta.trackAssignments[trkId]
      truthAssignmentIds = numpy.array(truthAssignments['TRUTH_IDS'])
      self.write('Track', trkId, 'assigned to truths:', truthAssignmentIds, '\\\\')
      idx = numpy.where(truthAssignmentIds >= 0)
      if numpy.size(idx) > 0:
        validTruthAssignments = truthAssignmentIds[idx]
        (uTruth, count) = numpy.unique(validTruthAssignments, return_counts=True)
        bestAssignedTruth = uTruth[numpy.argmax(count)]
        self.write('Track', trkId, 'best assigned truth:', bestAssignedTruth, os.linesep)
        (uTruth, count) = numpy.unique(truthAssignmentIds, return_counts=True)
        fig, ax = self._getSingleAxisFigure(xlabel='Time', ylabel='Assigned Truth', title='Track ' + str(trkId) + ' Assignments')
        for iUTruth, truthId in enumerate(uTruth):
          idx = numpy.squeeze(numpy.where(truthAssignmentIds == truthId))
          #print('trackAssignments:', trackAssignments)
          #print('idx:', idx, ' for truthId:', truthId)
          #print(validTimes)
          ax.plot(numpy.array(truthAssignments['TIME'])[idx], iUTruth * numpy.ones(numpy.shape(idx)), 's')
        ax.set(ylim=(-0.1, len(uTruth) - 0.9))
        ax.set(yticks=range(0, len(uTruth)), yticklabels=[str(truth) if truth >= 0 else 'Unassigned' for truth in uTruth])
        self._addFigures([fig], [''.join(('track', str(trkId), 'Assignments.pdf'))], 1)
        self._makeAssignedTrackAndTruthPlots(trkId, bestAssignedTruth)
      else:
        self.write('Track', trkId, 'never assigned to truth.', os.linesep)
      #print('Done with track', trkId)

  def _makeAssignedTrackAndTruthPlots(self, trkId, truthId):
    # Straight comparisons
    plotDims = self.plotDict['TRACK']
    figs = []
    names = []
    truthData = self.dta.truthManager.idMapData[truthId]
    trkData = self.dta.trackManager.idMapData[trkId]
    for plotDim in plotDims:
      xAxisTrk = self.dta.trackManager._timeField if plotDim[0] in ('T', 'TIME') else plotDim[0]
      yAxisTrk = self.dta.trackManager._timeField if plotDim[1] in ('T', 'TIME') else plotDim[1]
      xAxisTruth = self.dta.truthManager._timeField if plotDim[0] in ('T', 'TIME') else plotDim[0]
      yAxisTruth = self.dta.truthManager._timeField if plotDim[1] in ('T', 'TIME') else plotDim[1]
      fig, ax = self._getSingleAxisFigure(xlabel=xAxisTrk,
        ylabel=yAxisTrk,
        facecolor=(0.5, 0.5, 0.5),
        title='{0:s} vs {1:s} for truth {2:s} and track {3:s}'.format(xAxisTrk, yAxisTrk, str(truthId), str(trkId)))
      figs.append(fig)
      names.append('truth{2:d}WithTrack{3:d}_{0:s}vs{1:s}.pdf'.format(xAxisTrk, yAxisTrk, truthId, trkId))
      ax.plot(truthData[xAxisTruth], truthData[yAxisTruth], 'ko-', markeredgecolor='k', markersize=8)
      ax.plot(trkData[xAxisTrk], trkData[yAxisTrk], 'wo', markeredgecolor='w', markersize=5)
    self._addFigures(figs, names, 2)

    # Deltas with uncertainty
    plotDims = self.plotDict['ERROR']
    figs = []
    names = []
    truthData = self.dta.truthManager.idMapData[truthId]
    trkData = self.dta.trackManager.idMapData[trkId]
    for plotDim in plotDims:
      xAxisTrk = self.dta.trackManager._timeField if plotDim[0] in ('T', 'TIME') else plotDim[0]
      yAxisTrk = self.dta.trackManager._timeField if plotDim[1] in ('T', 'TIME') else plotDim[1]
      xAxisTruth = self.dta.truthManager._timeField if plotDim[0] in ('T', 'TIME') else plotDim[0]
      yAxisTruth = self.dta.truthManager._timeField if plotDim[1] in ('T', 'TIME') else plotDim[1]
      fig, ax = self._getSingleAxisFigure(xlabel=xAxisTrk,
        ylabel=yAxisTrk,
        facecolor=(0.5, 0.5, 0.5),
        title='{0:s} vs {1:s} Errors for truth {2:s} and track {3:s}'.format(xAxisTrk, yAxisTrk, str(truthId), str(trkId)))
      figs.append(fig)
      names.append('truth{2:d}WithTrack{3:d}Errors_{0:s}vs{1:s}.pdf'.format(xAxisTrk, yAxisTrk, truthId, trkId))
      if xAxisTrk == self.dta.trackManager._timeField:
        ax.plot(truthData[xAxisTruth], numpy.zeros(numpy.shape(truthData[xAxisTruth])), 'k-', markeredgecolor='k', markersize=8)
        interpTruth = numpy.interp(trkData[xAxisTrk], truthData[xAxisTruth], truthData[yAxisTruth], left=numpy.nan, right=numpy.nan) 
        ax.errorbar(trkData[xAxisTrk], trkData[yAxisTrk] - interpTruth,
            yerr=2.0*trkData['SIGMA_'+yAxisTrk], ecolor='w', markeredgecolor='w', linestyle='None', marker='o', markersize=5)
    self._addFigures(figs, names, 2)

  def _makeTruthAssignmentSummary(self):
    self.write('\\pagebreak')
    self.write('\\section{Truth Assignments}')
    times = self.dta.allTimeData.keys()
    allTruthIds = self.dta.truthManager.idMapData.keys()
    for iTruth, truthId in enumerate(allTruthIds):
      self.write('\\subsection{Truth', truthId, 'Assignments}')
      #print('Looking at truth', truthId)
      trkAssignments = self.dta.truthAssignments[truthId]
      trkAssignmentIds = numpy.array(trkAssignments['TRK_IDS'])
      idx = numpy.where(trkAssignmentIds >= 0)
      validTrackAssignments = trkAssignmentIds[idx]
      self.write('Truth', truthId, 'assigned to tracks:', trkAssignmentIds, '\\\\')
      (uTrk, count) = numpy.unique(validTrackAssignments, return_counts=True)
      bestAssignedTrack = uTrk[numpy.argmax(count)]
      self.write('Truth', truthId, 'best assigned track:', bestAssignedTrack, os.linesep)
      (uTrk, count) = numpy.unique(trkAssignmentIds, return_counts=True)
      fig, ax = self._getSingleAxisFigure(xlabel='Time', ylabel='Assigned Track', title='Truth ' + str(truthId) + ' Assignments')
      for iUTrk, trkId in enumerate(uTrk):
        idx = numpy.squeeze(numpy.where(trkAssignmentIds == trkId))
        #print('trackAssignments:', trackAssignments)
        #print('idx:', idx, ' for trkId:', trkId)
        #print(validTimes)
        ax.plot(numpy.array(trkAssignments['TIME'])[idx], iUTrk * numpy.ones(numpy.shape(idx)), 's')
      ax.set(ylim=(-0.1, len(uTrk) - 0.9))
      ax.set(yticks=range(0, len(uTrk)), yticklabels=[str(trk) if trk >= 0 else 'Unassigned' for trk in uTrk])
      self._addFigures([fig], [''.join(('truth', str(truthId), 'Assignments.pdf'))], 1)
      #print('Done with truth', truthId)

  def _addFigures(self, figs, names, numPerRow=1):
    self.write('\\begin{center}')
    self.write('\\begin{minipage}{\\textwidth}')
    width = str(7.0 / numPerRow - 0.2) + 'in'
    for fig, name in zip(figs, names):
      fullName = os.path.join(self.outDir, name)
      #print('Saving figure', name)
      fig.savefig(fullName)
      plt.close(fig)
      self.write('  \\includegraphics[width='+width+']{'+fullName+'}')
    self.write('\\end{minipage}')
    self.write('\\end{center}')

  def _getSingleAxisFigure(self, **kwargs):
    fig = plt.figure()
    ax = fig.add_subplot('111')
    ax.set(**kwargs)
    return (fig, ax)

  def _setDefaultLineCycle(self, ax):
    ax.set(prop_cycle=self.defaultLineCycler)

