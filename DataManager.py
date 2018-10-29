import numpy
import io
import os
import matplotlib.pyplot as plt

class DataManager:

  def __init__(self, filename, hasId=True):
    print('I am going to open file: %s' % (filename,))
    # The first line contains the field identifiers
    with io.open(filename, "r") as f:
      firstLine = f.readline().rstrip()
    # Read in the rest of the data
    rawData = numpy.double(numpy.loadtxt(filename, skiprows=1, comments=['#', '//']))
    #print(rawData)
    fldArray = firstLine.split()
    mapping = {}
    if 'T' in fldArray:
      self._timeField = 'T'
    elif 'TIME' in fldArray:
      self._timeField = 'TIME'
    else:
      raise RuntimeError('Unknown time field in:' + str(fldArray))
    for iFld, fld in enumerate(fldArray):
      mapping[fld] = rawData[:, iFld]
      if fld == 'ID':
        mapping[fld] = numpy.array(mapping[fld], numpy.int)
        print mapping[fld]
    self._uniqueTimes = numpy.unique(mapping[self._timeField])
    self.idMapData = {}
    if hasId:
      for uid in numpy.unique(mapping['ID']):
        # Use negative ID as heartbeat, so we get the complete time axis
        if uid < 0:
          continue
        intUid = int(uid)
        idx = numpy.where(mapping['ID'] == uid)
        self.idMapData[intUid] = {}
        for fld in fldArray:
          #print(iFld)
          self.idMapData[intUid][fld] = mapping[fld][idx]
      print(self.idMapData)
    else:
      self.idMapData[0] = mapping
    print('Done reading file: {0:s}'.format(filename))

  def getUniqueTimes(self):
    return self._uniqueTimes

  def interpolateToTimeAxis(self, timeAxis):
    for id, thisIdData in self.idMapData.items():
      for fld, fldData in thisIdData.items():
        # Must interpolate time field at the end, otherwise the other interpolations won't be correct
        if fld != self._timeField:
          self.idMapData[id][fld] = numpy.interp(timeAxis, thisIdData[self._timeField], fldData, left=numpy.nan, right=numpy.nan)
      self.idMapData[id][self._timeField] = timeAxis

  def getIndividualDataAtTime(self, data, time):
    returnData = None
    idx = (data[self._timeField] == time)
    count = numpy.count_nonzero(idx)
    if count == 0:
      pass
    elif count == 1:
      returnData = {}
      for fld, fldData in data.items():
        returnData[fld] = data[fld][idx]
    elif count > 1:
      raise RuntimeError('Track', data['ID'][idx[0]], 'has duplicate data at time', time)
    return returnData

if __name__ == '__main__':
  dm = DataManager('test.txt', hasId=False)
  print(dm.idMapData)
  plt.figure()
  plt.hold(True)
  legTxt = ()
  lines = ()
  for key, value in dm.idMapData.items():
    lines += plt.plot(value['X'], value['Y'], 'o-', label=str(key)),
  plt.xlabel('X')
  plt.ylabel('Y')
  plt.legend()
  plt.show()
