from pytest_bdd import scenario


@scenario('../features/update_shard_count_usual_case.feature',
          'Execute Digito-UpdateKinesisDataStreamsShardCount_2020-10-26 '
          'two times to increase the number of shards and decrease back')
def test_update_shard_count_increase_and_decrease():
    pass


@scenario('../features/update_shard_count_usual_case.feature',
          'Execute Digito-UpdateKinesisDataStreamsShardCount_2020-10-26 '
          'to pass the same number of shards as it was before')
def test_update_shard_count_pass_the_same_number_of_shards():
    pass
