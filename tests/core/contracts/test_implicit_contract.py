import pytest

from eth_utils import (
    is_integer,
)

from web3.contract import (
    ImplicitContract,
)


@pytest.fixture()
def math_contract(w3, MATH_ABI, MATH_CODE, MATH_RUNTIME, address_conversion_func):
    # Deploy math contract
    # NOTE Must use non-specialized contract factory or else deploy() doesn't work
    MathContract = w3.eth.contract(
        abi=MATH_ABI,
        bytecode=MATH_CODE,
        bytecode_runtime=MATH_RUNTIME,
    )
    tx_hash = MathContract.constructor().transact()
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    math_address = address_conversion_func(tx_receipt['contractAddress'])
    # Return interactive contract instance at deployed address
    # TODO Does parent class not implement 'deploy()' for a reason?
    MathContract = w3.eth.contract(
        abi=MATH_ABI,
        bytecode=MATH_CODE,
        bytecode_runtime=MATH_RUNTIME,
        ContractFactoryClass=ImplicitContract,
    )
    with pytest.warns(DeprecationWarning, match='deprecated in favor of contract.caller'):
        contract = MathContract(math_address)
        assert contract.address == math_address
        return contract


@pytest.fixture()
def get_transaction_count(w3):
    def get_transaction_count(blocknum_or_label):
        block = w3.eth.get_block(blocknum_or_label)
        # Return the blocknum if we requested this via labels
        # so we can directly query the block next time (using the same API call)
        # Either way, return the number of transactions in the given block
        if blocknum_or_label in ["pending", "latest", "earliest"]:
            return block.number, len(block.transactions)
        else:
            return len(block.transactions)
    return get_transaction_count


def test_implicitcontract_call_default(math_contract, get_transaction_count):
    # When a function is called that defaults to call
    blocknum, starting_txns = get_transaction_count("pending")
    with pytest.warns(DeprecationWarning, match='deprecated in favor of classic contract syntax'):
        start_count = math_contract.counter()
    assert is_integer(start_count)
    # Check that a call was made and not a transact
    # (Auto-mining is enabled, so query by block number)
    assert get_transaction_count(blocknum) == starting_txns
    # Check that no blocks were mined
    assert get_transaction_count("pending") == (blocknum, 0)


def test_implicitcontract_transact_default(math_contract, get_transaction_count):
    # Use to verify correct operation later on
    with pytest.warns(DeprecationWarning, match='deprecated in favor of classic contract syntax'):
        start_count = math_contract.counter()

    assert is_integer(start_count)  # Verify correct type
    # When a function is called that defaults to transact
    blocknum, starting_txns = get_transaction_count("pending")
    with pytest.warns(DeprecationWarning,
                      match='deprecated in favor of classic contract syntax') as warnings:
        math_contract.increment(transact={})
        # Check that a transaction was made and not a call
        assert math_contract.counter() - start_count == 1
        # Check that the correct number of warnings are raised
        assert len(warnings) == 2
    # (Auto-mining is enabled, so query by block number)
    assert get_transaction_count(blocknum) == starting_txns + 1
    # Check that only one block was mined
    assert get_transaction_count("pending") == (blocknum + 1, 0)


def test_implicitcontract_call_override(math_contract, get_transaction_count):
    # When a function is called with transact override that defaults to call
    blocknum, starting_txns = get_transaction_count("pending")
    with pytest.warns(DeprecationWarning, match='deprecated in favor of classic contract syntax'):
        math_contract.counter(transact={})
    # Check that a transaction was made and not a call
    # (Auto-mining is enabled, so query by block number)
    assert get_transaction_count(blocknum) == starting_txns + 1
    # Check that only one block was mined
    assert get_transaction_count("pending") == (blocknum + 1, 0)


def test_implicitcontract_transact_override(math_contract, get_transaction_count):
    # Use to verify correct operation later on
    with pytest.warns(DeprecationWarning, match='deprecated in favor of classic contract syntax'):
        start_count = math_contract.counter()
    assert is_integer(start_count)  # Verify correct type
    # When a function is called with call override that defaults to transact
    blocknum, starting_txns = get_transaction_count("pending")
    with pytest.warns(DeprecationWarning,
                      match='deprecated in favor of classic contract syntax') as warnings:
        math_contract.increment(call={})
        # Check that a call was made and not a transact
        assert math_contract.counter() - start_count == 0
        assert len(warnings) == 2
    # (Auto-mining is enabled, so query by block number)
    assert get_transaction_count(blocknum) == starting_txns
    # Check that no blocks were mined
    assert get_transaction_count("pending") == (blocknum, 0)


def test_implicitcontract_deprecation_warning(math_contract):
    with pytest.warns(DeprecationWarning, match='deprecated in favor of classic contract syntax'):
        math_contract.counter(transact={})
