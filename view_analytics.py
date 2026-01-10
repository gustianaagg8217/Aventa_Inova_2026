from analytics import TradingAnalytics
import sys

def main():
    print("\n" + "="*80)
    print("📊 TRADING BOT ANALYTICS VIEWER")
    print("="*80)
    
    analytics = TradingAnalytics('bot_trades.csv')
    
    while True:
        print("\n📋 MENU:")
        print("1.View Dashboard")
        print("2.Export JSON Report")
        print("3.Export Excel Report")
        print("4.View Last 30 Days")
        print("5.Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1': 
            analytics.print_dashboard()
        elif choice == '2': 
            analytics.export_report()
        elif choice == '3': 
            analytics.export_excel()
        elif choice == '4': 
            daily = analytics.get_daily_performance(30)
            if daily is not None and not daily.empty:
                print("\n" + "="*80)
                print("📅 LAST 30 DAYS PERFORMANCE")
                print("="*80)
                print(daily.to_string(index=False))
            else:
                print("\n⚠️  No daily data available")
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else: 
            print("\n❌ Invalid option")

if __name__ == "__main__": 
    main()