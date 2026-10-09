from pathlib import Path


def test_dashboard_displays_coverage_and_p01_status():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path('app.py').resolve()), default_timeout=30).run()
    assert not app.exception
    coverage = [table.value for table in app.dataframe if 'item_id' in table.value.columns]
    assert len(coverage) == 1
    assert {'implementation','tests','review','result'} <= set(coverage[0].columns)
    assert 'P01' in coverage[0].item_id.values
    assert any('módulo isolado' in item.value for item in app.markdown)
