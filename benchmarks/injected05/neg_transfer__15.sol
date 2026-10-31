pragma solidity 0.5.12;

contract Locker2831 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(deposits[msg.sender] >= amount);
        msg.sender.transfer(amount);
        deposits[msg.sender] -= amount;
        reserve -= amount;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
