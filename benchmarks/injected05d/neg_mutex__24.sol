pragma solidity 0.5.12;

contract Locker3216 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        balances[msg.sender] -= amount;
        total -= amount;
        locked = false;
    }
}
