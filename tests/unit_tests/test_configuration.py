from langgraph.pregel import Pregel

from agent.graph import graph
from agent.aliyun_action_trail_agent import  aliyun_action_trail_agent


def test_placeholder() -> None:
    # TODO: You can add actual unit tests
    # for your graph and other logic here.
    assert isinstance(graph, Pregel)
