pragma solidity 0.5.12;

contract Vault3078 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        total -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
