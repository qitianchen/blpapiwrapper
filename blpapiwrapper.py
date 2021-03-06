"""
Python wrapper to emulate Excel bdp and bdh through Bloomberg Open API

Written by Alexandre Almosni
"""


import blpapi
import datetime
import pandas

class BLP():

    def __init__(self):
        #Bloomberg session created only once here - makes consecutive bdp() and bdh() calls faster
        self.session = blpapi.Session()
        self.session.start()
        self.session.openService('//BLP/refdata')
        self.refDataSvc = self.session.getService('//BLP/refdata')

    def bdp(self, strSecurity='US900123AL40 Govt', strData='PX_LAST', strOverrideField='', strOverrideValue=''):
        request = self.refDataSvc.createRequest('ReferenceDataRequest')
        request.append('securities', strSecurity)
        request.append('fields',strData)
        if strOverrideField != '':
            o = request.getElement('overrides').appendElement()
            o.setElement('fieldId',strOverrideField)
            o.setElement('value',strOverrideValue)
        requestID = self.session.sendRequest(request)
        while True:
            event = self.session.nextEvent()
            if event.eventType() == blpapi.event.Event.RESPONSE:
                break
        output = blpapi.event.MessageIterator(event).next().getElement('securityData').getValueAsElement(0).getElement('fieldData').getElementAsString(strData)
        if output == '#N/A':
            output = pandas.np.nan
        return output

    def bdh(self, strSecurity='SPX Index', strData='PX_LAST', startdate=datetime.date(2014,1,1), enddate=datetime.date(2014,1,9), periodicity='DAILY'):
        request = self.refDataSvc.createRequest('HistoricalDataRequest')
        request.append('securities', strSecurity)
        if type(strData) == str:
            strData=[strData]
        for strD in strData:
            request.append('fields',strD)
        request.set('startDate',startdate.strftime('%Y%m%d'))
        request.set('endDate',enddate.strftime('%Y%m%d'))
        request.set('periodicitySelection', periodicity);
        requestID = self.session.sendRequest(request)
        while True:
            event = self.session.nextEvent()
            if event.eventType() == blpapi.event.Event.RESPONSE:
                break
        fieldDataArray = blpapi.event.MessageIterator(event).next().getElement('securityData').getElement('fieldData')
        fieldDataList = [fieldDataArray.getValueAsElement(i) for i in range(0,fieldDataArray.numValues())]
        outDates = [x.getElementAsDatetime('date') for x in fieldDataList]
        output = pandas.DataFrame(index=outDates,columns=strData)
        for strD in strData:
            output[strD] = [x.getElementAsFloat(strD) for x in fieldDataList]
        output.replace('#N/A History',pandas.np.nan,inplace=True)
        output.index = output.index.to_datetime()
        return output

    def bdhOHLC(self, strSecurity='SPX Index', startdate=datetime.date(2014,1,1), enddate=datetime.date(2014,1,9), periodicity='DAILY'):
        return self.bdh(strSecurity, ['PX_OPEN','PX_HIGH','PX_LOW','PX_LAST'], startdate, enddate, periodicity)

    def closeSession(self):
        self.session.stop()


def main():
    bloomberg=BLP()
    print bloomberg.bdp()
    print ''
    print bloomberg.bdp('US900123AL40 Govt','YLD_YTM_BID','PX_BID','200')
    print ''
    print bloomberg.bdh()
    print ''
    print bloomberg.bdhOHLC()
    bloomberg.closeSession()

if __name__ == '__main__':
    main()
