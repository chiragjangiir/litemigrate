from litemigrate.fts5_tokenizer_helper import Fts5TokenizerHelper

def test_fts5_tokenizer():
    clause1 = Fts5TokenizerHelper.build_tokenizer_clause("porter")
    assert clause1 == "tokenize = 'porter'"
    clause2 = Fts5TokenizerHelper.build_tokenizer_clause("unicode61", ["remove_diacritics 1", "tokenchars '_'"])
    assert clause2 == "tokenize = 'unicode61 remove_diacritics 1 tokenchars '_''"
