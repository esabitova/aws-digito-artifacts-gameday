from pytest_bdd import scenario


@scenario('../features/decrease_number_of_shards_usual_case.feature',
          'Execute Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21 in usual case')
def test_decrease_number_of_shards_usual_case():
    pass


@scenario('../features/decrease_number_of_shards_rollback_previous.feature',
          'Execute SSM automation document Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21 in rollback')
def test_decrease_number_of_shards_rollback_previous():
    pass


@scenario('../features/decrease_number_of_shards_failed.feature',
          'Execute SSM automation document Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21 '
          'to test failure case')
def test_decrease_number_of_shards_failed():
    pass
