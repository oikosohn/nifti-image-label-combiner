import base64
import gzip
from io import BytesIO, StringIO

import numpy as np
import nibabel as nib
import pandas as pd
import streamlit as st

from nibabel import FileHolder, Nifti1Image


def upload_nii_files():
    uploaded_files = st.file_uploader('Upload NII or NII.GZ files', type=['nii', 'nii.gz'], accept_multiple_files=True)
    return uploaded_files


def process_nii_files(uploaded_files, label_value):
    f = BytesIO()
    
    header, image, combined_file = None, None, None
    before_combine_label, after_combine_label = {}, {}
    for idx, uploaded_file in enumerate(uploaded_files):
        
        file_data = uploaded_file.read()
        file_obj = BytesIO(file_data)
        
        
        filename = uploaded_file.name

        if filename.endswith('gz'):
            file_holder = FileHolder(filename=filename, fileobj=gzip.GzipFile(fileobj=file_obj))
        else:
            file_holder = FileHolder(filename=filename, fileobj=file_obj)

        nifti_image = Nifti1Image.from_file_map({'header': file_holder, 'image': file_holder})
        
        value = nifti_image.get_fdata()
        
        before_combine_label[filename] = [np.unique(value), value.shape]
        
        if idx == 0:
            header = nifti_image
            image = value
            image[image != 0] = label_value
        else:
            image[value != 0] = label_value
        
    combined_file = nib.Nifti1Image(image, header.affine, header.header)    
    file_map = combined_file.make_file_map({'image': f, 'header': f})
    combined_file.to_file_map(file_map)
    combined_file = gzip.compress(f.getvalue())
    return combined_file, before_combine_label, image


def make_df(label_info):
    filenames, unique_values, image_shapes = [], [], []
    for name, (value, shape) in label_info.items():
        filenames.append(name)
        unique_values.append(value)
        image_shapes.append(shape)
        
    df = pd.DataFrame({'Filename': filenames, 'Unique Values': unique_values, 'Image Shape': image_shapes})
    return df
    
    
def main():
    st.title('NILC : NIfTI Image Label Combiner - Streamlit Demo')
    url = 'https://github.com/oikosohn/nifti-image-label-combiner/edit/streamlit/'
    st.markdown(f'This demo does not save your files. If you want code for local execution, please visit [this repository]({url}).')
    st.markdown(''' \n You can also find the streamlit demo code in [![Repo](https://badgen.net/badge/icon/GitHub?icon=github&label)](https://github.com/oikosohn/nifti-label-combiner/tree/streamlit) ''', unsafe_allow_html=True)
    st.header(':one: Upload files')
    
    
    uploaded_files = upload_nii_files()
    
    if uploaded_files is None or len(uploaded_files) == 0:
        st.info('No files uploaded.')
        return
    
    st.header(':two: Enter File Name and Value')
    
    output_filename = st.text_input('Enter File Name (Default name is your first label filename)', uploaded_files[0].name)
    label_value = st.text_input('Enter Label Value (Default value is 1)', 1)

                
    combined_file = None
    start_combine_button = st.button('Start Combine', use_container_width=True)
    
    if  uploaded_files and start_combine_button:
        combined_file, before_combine_label, after_combine_label = process_nii_files(uploaded_files, label_value)
        
        st.write('Unique value before combine')
        before_df = make_df(before_combine_label)
        st.write(before_df)
        
        if combined_file:
            st.header(':three: Download Combined Label files')
            st.success('Success in combining')
            
            st.write('Unique value after combine')
            if not output_filename.endswith('.nii.gz'):
                output_filename = output_filename + '.nii.gz'
            st.write(make_df({output_filename: [np.unique(after_combine_label), after_combine_label.shape]}))
            
            st.download_button(label='Download File', data=combined_file, file_name=output_filename, mime='application/gzip', use_container_width=True)
        else:
            st.error('Failure in combining')
            

if __name__ == '__main__':
    main()
