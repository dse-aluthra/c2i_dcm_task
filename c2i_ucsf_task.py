#!/usr/bin/env python
# coding: utf-8

# # UCSF Challenge
# ### Get all secondary capture images 
#     For PatientID(0010,0020) = PAT020 from DICOM server (https://www.dicomserver.co.uk/) 
# 
#     Server is at www.dicomserver.co.uk  and Ports are 104 and 11112

# ### Install dependancy libraries
# !pip install pynetdicom Or conda install -c conda-forge pynetdicom
# !pip install pydicom Or  conda install -c conda-forge pydicom
from pynetdicom import AE, VerificationPresentationContexts, build_context
from pynetdicom import AE, VerificationPresentationContexts
from pynetdicom.sop_class import VerificationSOPClass
from pynetdicom.sop_class import CTImageStorage
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelGet
from pynetdicom.sop_class import CTImageStorage
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelMove

from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelFind
from pynetdicom.sop_class import PatientStudyOnlyQueryRetrieveInformationModelFind
from pynetdicom.sop_class import GeneralRelevantPatientInformationQuery
from pynetdicom import  StoragePresentationContexts
from pydicom.dataset import Dataset, FileDataset
from pynetdicom import AE, evt, debug_logger, build_role
import time

SERVER_ADDRESS = 'www.dicomserver.co.uk'
PORT = 11112  #104
AE_TITLE = b'C2I_UCSF_SCU' 
DESCRIPTION='Storage SCP sample'

DEBUG_ON = True

def OnReceiveStore(SOPClass, DS):
    file_meta = Dataset()
    file_meta.PatientID = 'PAT020'
    filename = time.strftime("%Y%m%d_%H%M%S") + ".dcm"
    
    ds = FileDataset(filename, {}, file_meta=file_meta, preamble="\0" * 128)
    ds.update(DS)
    ds.save_as(filename)
    return SOPClass.Success

def handle_store(event):
    ds = event.dataset
    ds.file_meta = event.file_meta
    tmp_fname = time.strftime("%Y%m%d_%H%M%S") + ".dcm"
    
    ds.save_as(ds.SOPInstanceUID, write_like_original=False)
    return 0x0000

def create_queryDS(qrlevel = 'SERIES'):
    ds = Dataset()
    ds.QueryRetrieveLevel = qrlevel  #'IMAGE'
    ds.PatientID = 'PAT020'
    return ds


# # Option 1 : Query move service (SCU)
if DEBUG_ON:
    debug_logger()

def c_move_Option():
    print('Executing the C_MOVE approach i.e. SCU c_move')
    ae = AE(ae_title=AE_TITLE)
    ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)
    assoc = ae.associate(SERVER_ADDRESS, PORT)

    if assoc.is_established:
        responses = assoc.send_c_move(create_queryDS(), AE_TITLE, PatientRootQueryRetrieveInformationModelMove)
        for (status, identifier) in responses:
            if status:
                print('C-MOVE query status: 0x{0:04x}'.format(status.Status))
            else:
                print('Connection timed out, aborted or invalid response')

        assoc.release()
    else:
        print('Association rejected, aborted or never connected')


# # Option 2 : C_STORE Event handler (use)

def c_get_Option():
    print('Executing the C_GET approach i.e. SCU c_get')
    handlers = [(evt.EVT_C_STORE, handle_store)]
    CompositeInstanceRetrieveWithoutBulkDataGet = '1.2.840.10008.5.1.4.1.2.5.3'
    SecondaryCaptureImageStorage = '1.2.840.10008.5.1.4.1.1.7'

    ae = AE(ae_title=AE_TITLE)
    ae.add_requested_context(CompositeInstanceRetrieveWithoutBulkDataGet)
    ae.add_requested_context(SecondaryCaptureImageStorage)
    role = build_role(SecondaryCaptureImageStorage, scp_role=True)
    assoc = ae.associate(SERVER_ADDRESS, PORT, ext_neg=[role], evt_handlers=handlers)

    if assoc.is_established:
        responses = assoc.send_c_get(create_queryDS('IMAGE'), CompositeInstanceRetrieveWithoutBulkDataGet)
        for (status, identifier) in responses:
            if status:
                print('C-GET query status: 0x{0:04x}'.format(status.Status))
            else:
                print('Connection timed out, was aborted or received invalid response')

        assoc.release()
    else:
        print('Association rejected, aborted or never connected')

def main():
    """
    Main method to show two options to get images from DICOM server 
    Use SCU move or Event handler mechanism
    """
    c_move_Option()
    c_get_Option()
    print('Executed C-MOVE & C_GET with response status logged ')
    
    return


if __name__ == '__main__':
    main()
