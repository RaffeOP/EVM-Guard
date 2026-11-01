pragma solidity 0.5.12;

contract Bank7570 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function totalDeposits() public view returns (uint256) { return supply; }
}
