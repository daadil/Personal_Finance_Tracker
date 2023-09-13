import pandas as pd, glob
from datetime import datetime

# Global Variables
base_path = '/Users/juliawu/Desktop/David/'
account_type = ['Checking', 'Credit Card', 'Savings']
organization_name = ['Ally', 'American Express', 'Bank of America', 'Capital One', 'Chase', "Discover"]

credit_card_name = ['AMEX Delta', 'BoA Customized Cash Rewards', 'BoA Premium Rewards', 'CO Savor One', 'Discover',
                    'Chase Sapphire Preferred', 'Chase Amazon Prime']
credit_card_filepath = [base_path + account_type[1] + '/' + organization_name[2] + '/' + credit_card_name[2] + '/',
                        base_path + account_type[1] + '/' + organization_name[2] + '/' + credit_card_name[1] + '/',
                        base_path + account_type[1] + '/' + organization_name[3] + '/' + credit_card_name[3] + '/',
                        base_path + account_type[1] + '/' + organization_name[1] + '/' + credit_card_name[0] + '/',
                        base_path + account_type[1] + '/' + organization_name[5] + '/' + credit_card_name[4] + '/',
                        base_path + account_type[1] + '/' + organization_name[4] + '/' + credit_card_name[5] + '/',
                        base_path + account_type[1] + '/' + organization_name[4] + '/' + credit_card_name[6] + '/']


def create_cc_dfs(filepath, source):
    # print(filepath + "\n create cc function executed")
    df = []
    files = glob.glob(filepath + "/*.csv")
    for f in files:
        csv = pd.read_csv(f)
        df.append(csv)
    df = pd.concat(df)
    df = pd.DataFrame(df)

    if source == credit_card_name[2]:
        BoA_CC_Formatter(df)
    if source == credit_card_name[1]:
        BoA_CC_Formatter(df)
    if source == credit_card_name[3]:
        CO_CC_Formatter(df)  # TODO defination is not changing values correctly but does fire test0 print statement
    if source == credit_card_name[0]:
        AMEX_CC_Formatter(df)
    if source == credit_card_name[4]:
        Discover_CC_Formatter(df)
    if source == credit_card_name[5]:
        Chase_CC_Formatter(df)
    if source == credit_card_name[6]:
        Chase_CC_Formatter(df)
    df['Credit Card'] = [source for i in range(len(df))]
    df.sort_values(by=['Posted Date'])
    return df


def AMEX_CC_Formatter(df):
    return df


def BoA_CC_Formatter(df):
    df["Amount"] = (df["Amount"] * -1)
    df["Posted Date"] = df["Posted Date"].strftime('%Y-%m-%d')
    print(type(df))
    df.drop(df.columns[[1, 3]], axis=1, inplace=True)
    return df


def CO_CC_Formatter(df):
    df["Credit"] = (df["Credit"] * -1)
    df.rename(columns={"Debit": "Amount"}, inplace=True)
    df["Amount"] = df["Amount"].combine_first(df["Credit"].astype(
        float))  # keeps the columns but doesn't keep the negative https://www.datasciencelearner.com/how-to-merge-two-columns-in-pandas/#:~:text=How%20to%20Merge%20Two%20Columns%20in%20Pandas%20%3F,dataframe.%20...%203%20Step%203%3A%20Apply%20the%20approaches
    df.rename(columns={"Description": "Payee"}, inplace=True)
    df.drop(df.columns[[0, 2, 4, 6]], axis=1, inplace=True)
    return df


def Chase_CC_Formatter(df):
    df["Amount"] = (df["Amount"] * -1)
    df.rename(columns={"Description": "Payee"}, inplace=True)
    df.rename(columns={"Post Date": "Posted Date"}, inplace=True)
    df.drop(df.columns[[0, 3, 4, 6]], axis=1,
            inplace=True)  # TODO - Utilize "Type" column for logic, see raw data for column referance
    return df


def Discover_CC_Formatter(df):
    return df


try:
    BoA_Premium_Rewards_df = create_cc_dfs(credit_card_filepath[0], credit_card_name[2])
except:
    print("No data available. Creating blank df.")
    BoA_Premium_Rewards_df = []
try:
    BoA_Cash_Rewards_df = create_cc_dfs(credit_card_filepath[1], credit_card_name[1])
except:
    print("No data available. Creating blank df.")
    BoA_Cash_Rewards_df = []
try:
    CO_Savor_df = create_cc_dfs(credit_card_filepath[2], credit_card_name[3])
except:
    print("No data available. Creating blank df.")
    CO_Savor_df = []
try:
    AMEX_df = create_cc_dfs(credit_card_filepath[3], credit_card_name[0])
except:
    print("No data available. Creating blank df.")
    AMEX_df = []
try:
    Discover_df = create_cc_dfs(credit_card_filepath[4], credit_card_name[4])
except:
    print("No data available. Creating blank df.")
    Discover_df = []
try:
    Chase_Sapphire_df = create_cc_dfs(credit_card_filepath[5], credit_card_name[5])
except:
    print("No data available. Creating blank df.")
    Chase_Sapphire_df = []
try:
    Chase_Amazon_df = create_cc_dfs(credit_card_filepath[6], credit_card_name[6])
except:
    print("No data available. Creating blank df.")
    Chase_Amazon_df = []

# Merge dfs into one
# frames = [BoA_Premium_Rewards_df, BoA_Cash_Rewards_df, CO_Savor_df, Chase_Sapphire_df]
# all_Credit_Cards = pd.concat(frames)
# all_Credit_Cards = all_Credit_Cards.sort_values(by='Posted Date', ascending=False)

# Outputting Credit Cards to csv files
BoA_Premium_Rewards_df.to_csv(base_path + '/Output/BoA Premium Rewards Output.csv', index=False)
# BoA_Cash_Rewards_df.to_csv(base_path + '/Output/BoA Cash Rewards Output.csv', index=False)
# CO_Savor_df.to_csv(base_path + '/Output/CO Savor Output.csv', index=False)
# Chase_Sapphire_df.to_csv(base_path + '/Output/Chase Sapphire Output.csv', index=False)
# all_Credit_Cards.to_csv(base_path + '/Output/All Credit Cards Output.csv', index=False)

# Outputting Credit Cards data to a single xlsx file
# with pd.ExcelWriter(base_path + '/Output/All Credit Cards Output.xlsx', engine='xlsxwriter') as writer:
#     all_Credit_Cards.to_excel(writer, sheet_name='All Cards', index=False)
#     BoA_Premium_Rewards_df.to_excel(writer, sheet_name='BoA Premium', index=False)
#     BoA_Cash_Rewards_df.to_excel(writer, sheet_name='BoA Cash', index=False)
#     CO_Savor_df.to_excel(writer, sheet_name='CO Savor', index=False)
#     Chase_Sapphire_df.to_excel(writer, sheet_name='Chase Sapphire', index=False)
exit()

# TODO - Set all date data to Year-Month-Day
# TODO - Ingest remaining credit cards with raw formats
# TODO - Modify CC data so they are all in the similar format, Keep only posted date, payee, amount
#  (shown as a positive number for a charge), drop payments, handle returns
# TODO - Anticipate the next annual fee, create calendar reminder
# TODO - Ingest all checking accounts (setup similar to CC)
# TODO - Ingest all savings accounts (setup similar to CC)
# TODO - Get updated data
# TODO - Figure out way to categorize data
# TODO - For CC only, add transaction type and calculate cash or point transaction type logic (resturant = 3% back)
# TODO - For CC only, calculate the number of points/amount of cash back on purchase based on
#  type of purchase (resturant = 3% back)
# TODO - Graphically display all data and have it interactable (set filters)
# TODO - check data if it's stale, aka, if last posted date is greater than 45 days then alert the user with print
#  statement that says "possible stale data, please add newest csv"
