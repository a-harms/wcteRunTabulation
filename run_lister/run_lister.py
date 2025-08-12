#!/usr/bin/env python3



import pandas as pd
import json
from datetime import datetime



def filter_by_date(df, first_day, last_day, date_label):
    df_filtered = df.copy()
    df_filtered = df_filtered.loc[(df_filtered[date_label] >= first_day) & (df_filtered[date_label] <= last_day)]
    return df_filtered


def filter_by_momentum(df, momenta, momentum_label):
    df_filtered = df.iloc[:0].copy()
    
    for momentum in momenta:
        df_filtered = pd.concat([df_filtered, df.loc[df[momentum_label] == momentum].copy()])

    return df_filtered



# function to clean the Trigger Config column in the Beam Monitor Run Log (beam) dataFrame by reducing the list
# of trigger config file names to those used in the WCTE Calibration and Beam Run tracker (mpmt) dataFrame in
# order to enable comparison
def clean_trigger_config(df):
    df_filtered = df.copy()

    # LEP 5.0
    df_filtered = df_filtered.replace(to_replace='', value='LEP 5.0')

    # LEP 5.1
    df_filtered = df_filtered.replace(to_replace='LEMP v5.1', value='LEP 5.1')
    df_filtered = df_filtered.replace(to_replace='LEP v5.1', value='LEP 5.1') # already done
    df_filtered = df_filtered.replace(to_replace='lep_v51', value='LEP 5.1')

    # T0TOF 1.1
    df_filtered = df_filtered.replace(to_replace='T0TOF v1.1', value='T0TOF 1.1')
    df_filtered = df_filtered.replace(to_replace='T0TOFv1.1', value='T0TOF 1.1')
    
    # T0TOF 1.2
    df_filtered = df_filtered.replace(to_replace='T0TOF v1.2', value='T0TOF 1.2')

    # TP0.6 4.4
    df_filtered = df_filtered.replace(to_replace='TP0.6 v4.4', value='TP0.6 4.4')
    df_filtered = df_filtered.replace(to_replace='tp0.6 v44', value='TP0.6 4.4')

    # TP0.8 v4.4
    df_filtered = df_filtered.replace(to_replace='TP0.8 v4.4', value='TP0.8 v4.4') # already done
    df_filtered = df_filtered.replace(to_replace='TP08v4.4', value='TP0.8 v4.4')
    df_filtered = df_filtered.replace(to_replace='tp0.8 v44', value='TP0.8 v4.4')

    # TP1 v4.4
    df_filtered = df_filtered.replace(to_replace='TP1 v4.4', value='TP1 v4.4') # already done
    df_filtered = df_filtered.replace(to_replace='tp1 v44', value='TP1 v4.4') # already done

    # LEMB v5.1
    df_filtered = df_filtered.replace(to_replace='LEMB v5.1', value='LEMB v5.1') # already done

    # LEP9Li 2.0
    df_filtered = df_filtered.replace(to_replace='LEP9Li v2', value='LEP9Li 2.0')
    df_filtered = df_filtered.replace(to_replace='LEP9Li v2.0', value='LEP9Li 2.0')
    df_filtered = df_filtered.replace(to_replace='LEPLi9 v2.0', value='LEP9Li 2.0')

    # TP0.5 v4.4
    df_filtered = df_filtered.replace(to_replace='TP0.5 v4.4', value='TP0.5 v4.4') # already done
    df_filtered = df_filtered.replace(to_replace='TP05 v4.4', value='TP0.5 v4.4')

    # TPNH v4.4
    df_filtered = df_filtered.replace(to_replace='TPNH v4.4', value='TPNH v4.4') # already done

    # LEE v5.1
    df_filtered = df_filtered.replace(to_replace='LEE v5.1', value='LEE v5.1') # already done

    # TP0.65 v4.4
    df_filtered = df_filtered.replace(to_replace='TP0.65 v4.4', value='TP0.65 v4.4') # already done

    #unsure of what lep_v52, t0tof_v10 and t0_v43 should be converted to
    

    return df_filtered





def filter_by_trigger_config(df, trigger_configs, trigger_config_label):
    df_filtered = df.copy()

    df_filtered = df_filtered[df_filtered[trigger_config_label].isin(trigger_configs)]

    return df_filtered





def main():
    # set option to display all rows and columns when printing a dataFrame
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)


    config_filename = 'config.json'


    # load in the config file
    with open(config_filename) as config_file:
        config =  json.load(config_file)
    
    momenta = config['momenta']
    trigger_configs = config['trigger_configs']

    # create pandas datetime objects for filtering csv entries by date
    start_date = datetime.strptime(config['start_date'], '%m/%d/%y')
    end_date = datetime.strptime(config['end_date'], '%m/%d/%y')




    ########## Working with the Beam Monitor Run Log Spreadsheet ###########
    
    # reading in the Beam Monitor Run Log csv file
    df_beam_unconverted = pd.read_csv('./csv_files/Beam Monitor Run Log - 2025_Run_list.csv')

    df_beam = df_beam_unconverted.copy()

    # stripping leading and trailling whitespace from columns
    df_beam['Run number'].str.strip()
    df_beam['mpmt run'].str.strip()
    df_beam['Beam MeV/c'].str.strip()
    df_beam['Date'].str.strip()
    
    
    # casting data columns appropriately
    df_beam['Run number'] = pd.to_numeric(df_beam['Run number'], downcast='integer', errors='coerce')
    df_beam['mpmt run'] = pd.to_numeric(df_beam['mpmt run'], downcast='integer', errors='coerce')
    df_beam['Beam MeV/c'] = pd.to_numeric(df_beam['Beam MeV/c'], downcast='integer', errors='coerce')
    df_beam['Date'] = pd.to_datetime(df_beam['Date'], errors='coerce', dayfirst='True')
    

    # replace trigger config names for the ones used in the mpmt dataFrame for easier comparison
    df_beam = clean_trigger_config(df_beam)
    
    # generate lists of na values (includes empty values and values which may have been incorrectly parsed values during casting)
    with open("beam_na_lists.txt", "w") as f:
        print("List of empty and incorrectly parsed mpmt run number values", file=f)
        df_na = df_beam.loc[df_beam['mpmt run'].isna()]
        print(df_na[['Run number', 'mpmt run', 'Date', 'Trigger Config', 'Beam MeV/c']], file=f)

        print("\nList of empty and incorrectly parsed date values", file=f)
        df_na = df_beam.loc[df_beam['Date'].isna()]
        print(df_na[['Run number', 'mpmt run', 'Date', 'Trigger Config', 'Beam MeV/c']], file=f)
        
        print("\nList of empty and incorrectly parsed beam run number values", file=f)
        df_na = df_beam.loc[df_beam['Run number'].isna()]
        print(df_na[['Run number', 'mpmt run', 'Date', 'Trigger Config', 'Beam MeV/c']], file=f)
 
        print("\nList of empty and incorrectly parsed beam momentum values", file=f)
        df_na = df_beam.loc[df_beam['Beam MeV/c'].isna()]
        print(df_na[['Run number', 'mpmt run', 'Date', 'Trigger Config', 'Beam MeV/c']], file=f)



    #filter data
    df_beam = filter_by_date(df_beam, start_date, end_date, 'Date')
    df_beam = filter_by_momentum(df_beam, momenta, 'Beam MeV/c')
    df_beam = filter_by_trigger_config(df_beam, trigger_configs, 'Trigger Config')


    # output csv version of filtered beam runs
    #df_beam.to_csv("output_beam.csv")





    ########## Working with the WCTE Calibration and Beam Run tracker Spreadsheet ###########

    # reading in the WCTE Calibration and Beam Run tracker csv file
    df_mpmt_unconverted = pd.read_csv('./csv_files/modified_WCTE_Calibration_and_beam_run_tracker_2025_physics_data_page.csv')

    df_mpmt = df_mpmt_unconverted.copy()
    
    # stripping leading and trailling whitespace from columns
    #for column in df_mpmt:
    #    df_mpmt[column].str.strip()
    #    print(df_mpmt[column])

    df_mpmt['date (DD/MM)'].str.strip()
    df_mpmt['run number'].str.strip()
    df_mpmt['Beam momentum (MeV/c)'].str.strip()
    df_mpmt['vme run number'].str.strip()

    df_mpmt['trigger file type'].str.strip()

    df_mpmt['Run status'].str.strip()

    df_mpmt['ACT0'].str.strip()
    df_mpmt['ACT1'].str.strip()
    df_mpmt['ACT2'].str.strip()
    df_mpmt['ACT3'].str.strip()
    df_mpmt['ACT4'].str.strip()
    df_mpmt['ACT5'].str.strip()



    # delete all empty rows
    df_mpmt = df_mpmt.dropna(how='all')

    # casting data columns appropriately
    df_mpmt['run number'] = pd.to_numeric(df_mpmt['run number'], downcast='integer', errors='coerce') # mpmt run number
    
    df_mpmt['Beam momentum (MeV/c)'] = pd.to_numeric(df_mpmt['Beam momentum (MeV/c)'], downcast='integer', errors='coerce')

    df_mpmt['date (DD/MM)'] = pd.to_datetime(df_mpmt['date (DD/MM)'], errors='coerce', format="%d/%m")
    df_mpmt['date (DD/MM)'] = df_mpmt['date (DD/MM)'].apply(lambda x: x.replace(year = 2025)) # change datetime year from default 1900 to 2025 for all date values


    df_mpmt['vme run number'] = df_mpmt['vme run number'].str.extract('(\d+)') # extract beam run number from additional text
    df_mpmt['vme run number'] = pd.to_numeric(df_mpmt['vme run number'], downcast='integer', errors='coerce')



    # generate lists of na values (includes empty values and values which may have been incorrectly parsed values during casting)
    with open("mpmt_na_lists.txt", "w") as f:
        print("List of empty and incorrectly parsed mpmt run number values", file=f)
        df_na = df_mpmt.loc[df_mpmt['run number'].isna()]
        print(df_na[['vme run number', 'run number', 'date (DD/MM)', 'trigger file type', 'Beam momentum (MeV/c)']], file=f)

        print("List of empty and incorrectly parsed date values", file=f)
        df_na = df_mpmt.loc[df_mpmt['date (DD/MM)'].isna()]
        print(df_na[['vme run number', 'run number', 'date (DD/MM)', 'trigger file type', 'Beam momentum (MeV/c)']], file=f)
        
        print("List of empty and incorrectly parsed beam run number values", file=f)
        df_na = df_mpmt.loc[df_mpmt['vme run number'].isna()]
        print(df_na[['vme run number', 'run number', 'date (DD/MM)', 'trigger file type', 'Beam momentum (MeV/c)']], file=f)
 
        print("List of empty and incorrectly parsed beam momentum values", file=f)
        df_na = df_mpmt.loc[df_mpmt['Beam momentum (MeV/c)'].isna()]
        print(df_na[['vme run number', 'run number', 'date (DD/MM)', 'trigger file type', 'Beam momentum (MeV/c)']], file=f)



    #filter data
    df_mpmt = filter_by_date(df_mpmt, start_date, end_date, 'date (DD/MM)')
    df_mpmt = filter_by_momentum(df_mpmt, momenta, 'Beam momentum (MeV/c)')
    df_mpmt = filter_by_trigger_config(df_mpmt, trigger_configs, 'trigger file type')



    # output csv version of filtered beam runs
    #df_mpmt.to_csv("output_mpmt.csv")




    ####### Compare filtered DataFrames to find discrepancies ######

    # create smaller DataFrames with columns necessary for comparison
    df_beam_comparable = df_beam[['Run number', 'mpmt run', 'Date', 'Trigger Config', 'Beam MeV/c']]
    df_mpmt_comparable = df_mpmt[['vme run number', 'run number', 'date (DD/MM)', 'trigger file type', 'Beam momentum (MeV/c)']]

    # rename columns to have the same labels
    df_beam_comparable = df_beam_comparable.rename(columns={'Run number': 'vme run num', 'mpmt run': 'mpmt run num', 'Date': 'date', 'Trigger Config': 'trigger config', 'Beam MeV/c': 'momentum'})
    df_mpmt_comparable = df_mpmt_comparable.rename(columns={'vme run number': 'vme run num', 'run number': 'mpmt run num', 'date (DD/MM)': 'date', 'trigger file type': 'trigger config', 'Beam momentum (MeV/c)': 'momentum'})


    # list runs inconsistent between the two dataFrames

    df_beam_unmatched = pd.concat([df_beam_comparable, df_mpmt_comparable, df_mpmt_comparable]).drop_duplicates(keep=False)
    with open("beam_unmatched_runs.txt", "w") as f:
        print("runs from the Beam Monitor Run Log - 2025_Run_list spreadsheet inconsistent with the modified_WCTE_Calibration_and_beam_run_tracker_2025_physics_data_page spreadsheet: ", file=f)
        print(df_beam_unmatched, file=f)
        
    df_mpmt_unmatched = pd.concat([df_mpmt_comparable, df_beam_comparable, df_beam_comparable]).drop_duplicates(keep=False)
    with open("mpmt_unmatched_runs.txt", "w") as f:
        print("runs from the modified_WCTE_Calibration_and_beam_run_tracker_2025_physics_data_page  spreadsheet inconsistent with the Beam Monitor Run Log - 2025_Run_list spreadsheet: ", file=f)
        print(df_mpmt_unmatched, file=f)


    # consistent/final run list
    df_final = pd.merge(df_beam_comparable, df_mpmt_comparable, how='inner')
    df_final.to_csv("consistent_runs.csv")



if __name__=="__main__":
    main()
