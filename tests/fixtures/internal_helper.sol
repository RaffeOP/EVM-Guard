pragma solidity 0.4.24;

// The call sits in an internal helper used by two functions; the write follows the return.
contract InternalHelper {
    mapping(address => uint256) public rewards;
    mapping(address => bool) public claimed;

    function payOut(address to) internal {
        uint256 amount = rewards[to];
        rewards[to] = 0;
        require(to.call.value(amount)());
    }

    function withdraw() public {
        payOut(msg.sender);
    }

    function claimBonus() public {
        require(!claimed[msg.sender]);
        rewards[msg.sender] += 100;
        payOut(msg.sender);
        claimed[msg.sender] = true;
    }
}
