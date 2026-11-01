pragma solidity 0.5.12;

// The lock shares a slot with the owner, so it is written through a masked read-modify-write.
// Re-entry reverts at the lock check, so this is not reentrancy.
contract PackedMutex {
    address public owner;
    bool private locked;
    mapping(address => uint256) public balances;

    modifier nonReentrant() {
        require(!locked);
        locked = true;
        _;
        locked = false;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() public nonReentrant {
        uint256 amount = balances[msg.sender];
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        balances[msg.sender] = 0;
    }
}
