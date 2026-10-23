import argparse,json
from .engine import run
from .storage import connect,add_purchase
from .config import Settings
def main():
    parser=argparse.ArgumentParser(description='Read-only long-term advisor')
    sub=parser.add_subparsers(dest='command')
    sub.add_parser('report')
    buy=sub.add_parser('record-buy',help='Manually record gross executed purchase for monthly budget')
    buy.add_argument('--date',required=True,help='YYYY-MM-DD')
    buy.add_argument('--symbol',required=True)
    buy.add_argument('--amount',type=float,required=True)
    args=parser.parse_args()
    if args.command=='record-buy':
        db=connect(Settings().db)
        add_purchase(db,args.date,args.symbol,args.amount)
        db.close()
        print('Recorded. Check for duplicate manual entries before proceeding.')
    else: print(json.dumps(run(),indent=2,default=str))
if __name__=='__main__': main()
