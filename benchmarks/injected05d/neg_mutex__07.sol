pragma solidity 0.5.12;

contract Safe9226 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(deposits[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        deposits[msg.sender] -= amount;
        total -= amount;
        locked = false;
    }
}
