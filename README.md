# Gold Liquidity Map (XAUUSD)

بحث «سحب السيولة» على الذهب، ومواصفات مؤشر TradingView مبنية على نتائجه.

هذا المشروع يعيش على الفرع `gold-liquidity-map` في مستودع crypto-signals، منفصلاً تماماً عن `main` ومشروع الكريبتو: لا ملفات مشتركة ولا تاريخ مشترك.

- **ابدأ من هنا:** [GOLD_LIQUIDITY_INDICATOR_SPEC.md](GOLD_LIQUIDITY_INDICATOR_SPEC.md). فيه الملخص، والنتائج بالأرقام، ومواصفات المؤشر (Pine Script v6)، والبرومبت الجاهز لـ Claude Fable.
- **الصور:** أمثلة حقيقية للسحب ونموذج لشكل المؤشر في `research/examples/`.
- **البحث قابل لإعادة الإنتاج:**

```bash
pip install -r research/requirements.txt
python research/run_study.py       # كل الأرقام في research/results/
python research/plot_examples.py   # الصور في research/examples/
```

Research on liquidity sweeps in gold (OANDA:XAUUSD, 15m) and the spec for a TradingView indicator built on the findings. Start with `GOLD_LIQUIDITY_INDICATOR_SPEC.md` (Arabic).
